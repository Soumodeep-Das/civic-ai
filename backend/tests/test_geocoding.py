import asyncio

import httpx
import pytest

from civicai.domain import LocationPrecision
from civicai.geocoding import (
    GeocodingUnavailable, MapTilerGeocoder, NominatimGeocoder,
    normalize_maptiler_results, normalize_nominatim_results,
)


def test_normalize_nominatim_results_skips_invalid_and_preserves_precision():
    results = normalize_nominatim_results([
        {"place_id": 1, "display_name": "Baranagar, West Bengal", "lat": "22.64", "lon": "88.37", "addresstype": "city"},
        {"place_id": 2, "display_name": "Municipal office", "lat": "22.65", "lon": "88.38", "addresstype": "amenity"},
        {"place_id": 3, "display_name": "Outside range", "lat": "122", "lon": "88", "addresstype": "road"},
        {"unexpected": "value"},
    ])
    assert [(result.provider_id, result.precision) for result in results] == [
        ("1", LocationPrecision.BROAD),
        ("2", LocationPrecision.APPROXIMATE),
    ]


def test_nominatim_adapter_identifies_app_restricts_country_and_caches():
    requests = []

    async def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[{
            "place_id": 10,
            "display_name": "Baranagar, West Bengal, India",
            "lat": "22.64",
            "lon": "88.37",
            "addresstype": "city",
        }])

    geocoder = NominatimGeocoder(
        "https://geocoder.invalid",
        "CivicAI-Test/1.0",
        "in",
        minimum_interval_seconds=0,
        transport=httpx.MockTransport(handler),
    )

    async def run():
        first = await geocoder.search("Baranagar")
        second = await geocoder.search("  baranagar ")
        return first, second

    first, second = asyncio.run(run())
    assert first == second
    assert len(requests) == 1
    assert requests[0].headers["user-agent"] == "CivicAI-Test/1.0"
    assert requests[0].url.params["countrycodes"] == "in"
    assert requests[0].url.params["limit"] == "5"


def test_nominatim_adapter_sanitizes_bad_provider_payload():
    async def handler(request):
        return httpx.Response(200, json={"not": "a result list"})

    geocoder = NominatimGeocoder(
        "https://geocoder.invalid", "CivicAI-Test/1.0", "in",
        minimum_interval_seconds=0, transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GeocodingUnavailable):
        asyncio.run(geocoder.search("Baranagar"))


def test_nominatim_reverse_is_explicit_and_normalized():
    requests = []

    async def handler(request):
        requests.append(request)
        return httpx.Response(200, json={
            "place_id": 11, "display_name": "BT Road, Baranagar, India",
            "lat": "22.65", "lon": "88.38", "addresstype": "road",
        })

    geocoder = NominatimGeocoder(
        "https://geocoder.invalid", "CivicAI-Test/1.0", "in",
        minimum_interval_seconds=0, transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(geocoder.reverse(22.65, 88.38))
    assert result and result.label == "BT Road, Baranagar, India"
    assert requests[0].url.path == "/reverse"
    assert geocoder.autocomplete_supported is False


def test_normalize_maptiler_results_skips_invalid_and_limits_precision():
    results = normalize_maptiler_results({"features": [
        {"id": "place.1", "place_name": "Baranagar, West Bengal, India", "center": [88.37, 22.64], "place_type": ["municipality"]},
        {"id": "address.2", "place_name": "10 BT Road, Baranagar", "geometry": {"coordinates": [88.38, 22.65]}, "place_type": ["address"]},
        {"id": "bad", "place_name": "Bad coordinate", "center": [188, 22], "place_type": ["address"]},
    ]})
    assert [(item.provider_id, item.precision) for item in results] == [
        ("place.1", LocationPrecision.BROAD),
        ("address.2", LocationPrecision.APPROXIMATE),
    ]


def test_maptiler_adapter_autocomplete_country_proximity_and_reverse():
    requests = []

    async def handler(request):
        requests.append(request)
        label = "BT Road, Baranagar, India" if "," in request.url.path else "Baranagar, West Bengal, India"
        return httpx.Response(200, json={"features": [{
            "id": "address.1", "place_name": label,
            "center": [88.38, 22.65], "place_type": ["address"],
        }]})

    geocoder = MapTilerGeocoder(
        "https://api.maptiler.invalid", "secret-key", "in", "88.36,22.57",
        transport=httpx.MockTransport(handler),
    )

    async def run():
        return await geocoder.search("BT Road / Baranagar"), await geocoder.reverse(22.65, 88.38)

    searched, reversed_result = asyncio.run(run())
    assert searched[0].label == "Baranagar, West Bengal, India"
    assert reversed_result and reversed_result.label == "BT Road, Baranagar, India"
    assert geocoder.autocomplete_supported is True
    assert requests[0].url.raw_path.decode().split("?", 1)[0].endswith("/geocoding/BT%20Road%20%2F%20Baranagar.json")
    assert requests[0].url.params["autocomplete"] == "true"
    assert requests[0].url.params["country"] == "in"
    assert requests[0].url.params["proximity"] == "88.36,22.57"
    assert requests[1].url.path.endswith("/geocoding/88.3800000,22.6500000.json")


def test_maptiler_requires_key_and_sanitizes_failures():
    with pytest.raises(ValueError):
        MapTilerGeocoder("https://api.maptiler.invalid", "", "in")

    async def handler(request):
        return httpx.Response(429, json={"message": "quota"})

    geocoder = MapTilerGeocoder(
        "https://api.maptiler.invalid", "secret-key", "in",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GeocodingUnavailable):
        asyncio.run(geocoder.search("Baranagar"))
