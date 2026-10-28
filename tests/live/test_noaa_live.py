"""The clients against NOAA's APIs: a forecast from a point, observations, paging, async,
and typed models validating real responses."""

import asyncio
import itertools

import pytest
from apiroute import UnexpectedResponse

# Kansas City International: an airport, an observation station and a forecast office's area
LATITUDE, LONGITUDE = 39.2976, -94.7139
STATION = "KMCI"


@pytest.fixture(scope="module")
def point(weather):
    return weather.points.models.get(latitude=LATITUDE, longitude=LONGITUDE).properties


def test_a_point_leads_to_its_forecasts(weather, point):
    forecast = weather.gridpoints.models.forecast(point.grid_id, point.grid_x, point.grid_y)
    assert forecast.properties.periods[0].detailed_forecast
    # hourly periods carry windDirection, which is "" in a calm: outside the spec's enum
    hourly = weather.gridpoints.models.forecast_hourly(point.grid_id, point.grid_x, point.grid_y)
    assert len(hourly.properties.periods) > 24


def test_observations_and_stations(weather):
    latest = weather.stations.models.latest_observation(STATION).properties
    assert latest.station.endswith(f"/stations/{STATION}")
    assert weather.stations.models.get(STATION).properties.station_identifier == STATION


def test_list_all_pages_past_the_first_page(weather):
    pages = weather.stations.models.observations_all(STATION, limit=2)
    observations = list(itertools.islice(pages, 5))
    assert len(observations) == 5  # three pages of two
    assert len({o.properties.timestamp for o in observations}) == 5
    stations = list(itertools.islice(weather.stations.list_all(state=["KS"], limit=3), 7))
    assert len({s["id"] for s in stations}) == 7


def test_alerts(weather):
    assert weather.alerts.active_count()["total"] >= 0
    assert weather.alerts.models.active(area=["KS", "MO"]).features is not None


def test_async(weather, point):
    office = asyncio.run(weather.offices.models.aio.get(point.grid_id))
    assert office.id.endswith(f"/offices/{point.grid_id}")


def test_an_error_is_an_unexpected_response(weather):
    with pytest.raises(UnexpectedResponse) as raised:
        weather.stations.get("NOSUCHSTATION")
    assert raised.value.response.status_code == 404


def test_aviation_reports(aviation):
    [metar] = aviation.models.metar(ids=STATION, format="json")
    assert metar.icao_id == STATION and metar.raw_ob.startswith(("METAR", "SPECI", STATION))
    [taf] = aviation.models.taf(ids=STATION, format="json")
    assert taf.icao_id == STATION and taf.fcsts
    [station] = aviation.models.station_info(ids=STATION, format="json")
    assert station.icao_id == STATION


def test_water_gauges(water):
    gauge = water.gauges.models.get("PTTP1")
    assert gauge.name == "Ohio River at Pittsburgh"
    assert water.gauges.models.stage_flow_product("PTTP1", "observed").data is not None
