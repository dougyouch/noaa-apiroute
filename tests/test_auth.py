"""NoaaAuth: the User-Agent, weather.gov's API key, hosts, and retrying read-only POSTs."""

import httpx
import pytest
from apiroute import Retries

from noaa_apiroute.auth import DEFAULT_USER_AGENT
from noaa_apiroute.aviation import AviationWeatherApi
from noaa_apiroute.water import WaterApi
from noaa_apiroute.weather import WeatherApi


@pytest.fixture
def weather(transport):
    return WeatherApi(transport=transport)


def test_the_default_user_agent_and_no_key(weather, recorder):
    weather.points.get(latitude=39.7456, longitude=-97.0892)
    request = recorder.last
    assert str(request.url) == "https://api.weather.gov/points/39.7456,-97.0892"
    assert request.headers["User-Agent"] == DEFAULT_USER_AGENT
    assert "API-Key" not in request.headers


def test_your_user_agent_and_key(transport, recorder):
    weather = WeatherApi(user_agent="myapp (me@example.com)", api_key="k1", transport=transport)
    weather.gridpoints.forecast("TOP", 32, 81)
    assert str(recorder.last.url) == "https://api.weather.gov/gridpoints/TOP/32,81/forecast"
    assert recorder.last.headers["User-Agent"] == "myapp (me@example.com)"
    assert recorder.last.headers["API-Key"] == "k1"


def test_every_client_sends_the_user_agent_to_its_host(transport, recorder):
    AviationWeatherApi(user_agent="a", transport=transport).metar(ids="KMCI", format="json")
    assert (
        str(recorder.last.url) == "https://aviationweather.gov/api/data/metar?ids=KMCI&format=json"
    )
    assert recorder.last.headers["User-Agent"] == "a"
    WaterApi(user_agent="w", transport=transport).gauges.get("PTTP1")
    assert str(recorder.last.url) == "https://api.water.noaa.gov/nwps/v1/gauges/PTTP1"
    assert recorder.last.headers["User-Agent"] == "w"


def test_alerts_page_through_pagination_next(weather, recorder):
    next_url = "https://api.weather.gov/alerts?limit=1&cursor=abc"
    recorder.respond(
        httpx.Response(200, json={"features": [{"id": "a1"}], "pagination": {"next": next_url}}),
        httpx.Response(200, json={"features": [{"id": "a2"}]}),
    )
    assert [alert["id"] for alert in weather.alerts.list_all(limit=1)] == ["a1", "a2"]
    assert str(recorder.last.url) == next_url


def test_read_only_posts_are_retried_after_a_timeout(transport, recorder):
    water = WaterApi(transport=transport).with_options(retries=Retries(attempts=2, sleep=0))
    recorder.respond(httpx.ReadTimeout("slow"), httpx.Response(200, json={}))
    water.gauges.river_at_a_glance(body={"gaugeIds": ["PTTP1"]})
    assert len(recorder.requests) == 2
    assert recorder.last.method == "POST"
