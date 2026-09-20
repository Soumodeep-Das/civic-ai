import asyncio

import httpx
import pytest

from civicai.domain import LocationPrecision
from civicai.geocoding import GeocodingUnavailable, NominatimGeocoder, normalize_nominatim_results


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
