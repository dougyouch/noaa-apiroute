"""Live tests: calls to NOAA's APIs, run only when NOAA_LIVE=1.

    NOAA_LIVE=1 uv run pytest tests/live

They check requests and typed models against what NOAA actually sends. NOAA's APIs need no
key; the tests send a User-Agent naming this project, as weather.gov asks.
"""

import os

import pytest

from noaa_apiroute.aviation import AviationWeatherApi
from noaa_apiroute.water import WaterApi
from noaa_apiroute.weather import WeatherApi

LIVE = os.environ.get("NOAA_LIVE") == "1"
USER_AGENT = "noaa-apiroute live tests (https://github.com/dougyouch/noaa-apiroute)"


def pytest_collection_modifyitems(items):
    if LIVE:
        return
    for item in items:
        if "tests/live/" in item.nodeid:
            item.add_marker(pytest.mark.skip(reason="live tests run with NOAA_LIVE=1"))


@pytest.fixture(scope="session")
def weather() -> WeatherApi:
    return WeatherApi(user_agent=USER_AGENT)


@pytest.fixture(scope="session")
def aviation() -> AviationWeatherApi:
    return AviationWeatherApi(user_agent=USER_AGENT)


@pytest.fixture(scope="session")
def water() -> WaterApi:
    return WaterApi(user_agent=USER_AGENT)
