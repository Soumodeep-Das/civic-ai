import asyncio
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from time import monotonic
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from civicai.domain import LocationPrecision


class GeocodingUnavailable(Exception):
    """The configured search provider could not return a safe response."""


@dataclass(frozen=True)
class LocationCandidate:
    provider_id: str
    label: str
    latitude: float
    longitude: float
    precision: LocationPrecision


class Geocoder(Protocol):
    autocomplete_supported: bool

    async def search(self, query: str) -> Sequence[LocationCandidate]: ...

    async def reverse(self, latitude: float, longitude: float) -> LocationCandidate | None: ...


_BROAD_ADDRESS_TYPES = {
    "city", "country", "county", "district", "municipality", "postcode",
    "state", "state_district", "suburb", "town", "village",
}


def normalize_nominatim_results(payload: Any) -> list[LocationCandidate]:
    if not isinstance(payload, list):
        raise GeocodingUnavailable

    results: list[LocationCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            latitude = float(item["lat"])
            longitude = float(item["lon"])
            label = str(item["display_name"]).strip()
            provider_id = str(item["place_id"])
        except (KeyError, TypeError, ValueError):
            continue
        if not label or not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            continue
        address_type = str(item.get("addresstype") or item.get("type") or "").lower()
        precision = LocationPrecision.BROAD if address_type in _BROAD_ADDRESS_TYPES else LocationPrecision.APPROXIMATE
        results.append(LocationCandidate(provider_id, label[:300], latitude, longitude, precision))
    return results[:5]


def normalize_maptiler_results(payload: Any) -> list[LocationCandidate]:
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise GeocodingUnavailable

    results: list[LocationCandidate] = []
    for item in payload["features"]:
        if not isinstance(item, dict):
            continue
        try:
            provider_id = str(item["id"])
            label = str(item["place_name"]).strip()
            center = item.get("center") or item["geometry"]["coordinates"]
            longitude, latitude = float(center[0]), float(center[1])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if not provider_id or not label or not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            continue
        place_types = {str(value).lower() for value in item.get("place_type", [])}
        precision = LocationPrecision.BROAD if place_types & _BROAD_ADDRESS_TYPES else LocationPrecision.APPROXIMATE
        results.append(LocationCandidate(provider_id[:200], label[:300], latitude, longitude, precision))
    return results[:8]


class NominatimGeocoder:
    """Small policy-aware adapter for explicit, user-triggered searches."""

    autocomplete_supported = False

    def __init__(
        self,
        base_url: str,
        user_agent: str,
        country_codes: str,
        *,
        timeout_seconds: float = 8,
        minimum_interval_seconds: float = 1,
        cache_ttl_seconds: float = 900,
        cache_size: int = 128,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.country_codes = country_codes
        self.timeout_seconds = timeout_seconds
        self.minimum_interval_seconds = minimum_interval_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_size = cache_size
        self.transport = transport
        self._lock = asyncio.Lock()
        self._last_request_started = 0.0
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    async def search(self, query: str) -> Sequence[LocationCandidate]:
        key = "search:" + " ".join(query.split()).casefold()
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": "1",
            "dedupe": "1",
            "limit": "5",
            "accept-language": "en",
        }
        if self.country_codes:
            params["countrycodes"] = self.country_codes
        payload = await self._request("search", params, key)
        return normalize_nominatim_results(payload)

    async def reverse(self, latitude: float, longitude: float) -> LocationCandidate | None:
        key = f"reverse:{latitude:.6f},{longitude:.6f}"
        payload = await self._request("reverse", {
            "lat": f"{latitude:.7f}",
            "lon": f"{longitude:.7f}",
            "format": "jsonv2",
            "addressdetails": "1",
            "zoom": "18",
            "accept-language": "en",
        }, key)
        results = normalize_nominatim_results([payload])
        return results[0] if results else None

    async def _request(self, path: str, params: dict[str, str], key: str) -> Any:
        now = monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] <= self.cache_ttl_seconds:
            self._cache.move_to_end(key)
            return cached[1]

        async with self._lock:
            now = monotonic()
            cached = self._cache.get(key)
            if cached and now - cached[0] <= self.cache_ttl_seconds:
                self._cache.move_to_end(key)
                return cached[1]

            wait_seconds = self.minimum_interval_seconds - (now - self._last_request_started)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._last_request_started = monotonic()

            try:
                async with httpx.AsyncClient(
                    transport=self.transport,
                    timeout=self.timeout_seconds,
                    headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                ) as client:
                    response = await client.get(f"{self.base_url}/{path}", params=params)
                    response.raise_for_status()
                    payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise GeocodingUnavailable from exc

            self._cache[key] = (monotonic(), payload)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
            return payload


class MapTilerGeocoder:
    """MapTiler adapter for autocomplete, forward search and reverse lookup."""

    autocomplete_supported = True

    def __init__(
        self,
        base_url: str,
        api_key: str,
        country_codes: str,
        proximity: str = "",
        *,
        timeout_seconds: float = 8,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if not api_key:
            raise ValueError("MAPTILER_API_KEY is required when GEOCODING_PROVIDER=maptiler")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.country_codes = country_codes
        self.proximity = proximity
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def search(self, query: str) -> Sequence[LocationCandidate]:
        params = {
            "key": self.api_key,
            "language": "en",
            "limit": "8",
            "autocomplete": "true",
            "fuzzyMatch": "true",
        }
        if self.country_codes:
            params["country"] = self.country_codes
        if self.proximity:
            params["proximity"] = self.proximity
        payload = await self._request(quote(query, safe=""), params)
        return normalize_maptiler_results(payload)

    async def reverse(self, latitude: float, longitude: float) -> LocationCandidate | None:
        params = {"key": self.api_key, "language": "en", "limit": "1"}
        payload = await self._request(f"{longitude:.7f},{latitude:.7f}", params)
        results = normalize_maptiler_results(payload)
        return results[0] if results else None

    async def _request(self, location: str, params: dict[str, str]) -> Any:
        try:
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=self.timeout_seconds,
                headers={"Accept": "application/json"},
            ) as client:
                response = await client.get(f"{self.base_url}/geocoding/{location}.json", params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GeocodingUnavailable from exc
