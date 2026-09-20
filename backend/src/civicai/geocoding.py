import asyncio
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from time import monotonic
from typing import Any, Protocol

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
    async def search(self, query: str) -> Sequence[LocationCandidate]: ...


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


class NominatimGeocoder:
    """Small policy-aware adapter for explicit, user-triggered searches."""

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
        self._cache: OrderedDict[str, tuple[float, list[LocationCandidate]]] = OrderedDict()

    async def search(self, query: str) -> Sequence[LocationCandidate]:
        key = " ".join(query.split()).casefold()
        now = monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] <= self.cache_ttl_seconds:
            self._cache.move_to_end(key)
            return list(cached[1])

        async with self._lock:
            now = monotonic()
            cached = self._cache.get(key)
            if cached and now - cached[0] <= self.cache_ttl_seconds:
                self._cache.move_to_end(key)
                return list(cached[1])

            wait_seconds = self.minimum_interval_seconds - (now - self._last_request_started)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._last_request_started = monotonic()

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

            try:
                async with httpx.AsyncClient(
                    transport=self.transport,
                    timeout=self.timeout_seconds,
                    headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                ) as client:
                    response = await client.get(f"{self.base_url}/search", params=params)
                    response.raise_for_status()
                    results = normalize_nominatim_results(response.json())
            except (httpx.HTTPError, ValueError, GeocodingUnavailable) as exc:
                raise GeocodingUnavailable from exc

            self._cache[key] = (monotonic(), results)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
            return list(results)
