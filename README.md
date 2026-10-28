# noaa-apiroute

[![Build](https://github.com/dougyouch/noaa-apiroute/actions/workflows/build.yml/badge.svg)](https://github.com/dougyouch/noaa-apiroute/actions/workflows/build.yml)
[![Release](https://github.com/dougyouch/noaa-apiroute/actions/workflows/release.yml/badge.svg)](https://github.com/dougyouch/noaa-apiroute/actions/workflows/release.yml)

Python clients for NOAA's weather APIs: the [National Weather Service API](https://www.weather.gov/documentation/services-web-api) (api.weather.gov: forecasts, alerts, observations, stations, zones, radar, text products), the [AviationWeather.gov Data API](https://aviationweather.gov/data/api/) (METARs, TAFs, PIREPs, SIGMETs, airports) and the [National Water Prediction Service API](https://api.water.noaa.gov/nwps/v1/docs/) (river gauges, stage and flow forecasts). They're generated with [apiroute](https://github.com/dougyouch/apiroute) from NOAA's published OpenAPI specs and kept current by a weekly build.

- **Two layers:** every call works with plain dicts (`weather.points.get(...)`), and `.models` returns typed pydantic models (`weather.points.models.get(...)`).
- **Sync and async:** add `.aio` to any call for the async version.
- **Lazy loading:** only the APIs, sections and models you use are imported.
- **Typed:** the package ships `py.typed`.

## Installation

```bash
pip install noaa-apiroute    # or: uv add noaa-apiroute
```

It needs Python 3.10 or newer.

## Usage

### Forecasts, observations and alerts (api.weather.gov)

```python
from noaa_apiroute.weather import WeatherApi

weather = WeatherApi(user_agent="myapp (me@example.com)")

# A forecast starts from a point: it names the forecast office and grid square
point = weather.points.models.get(latitude=39.7456, longitude=-97.0892).properties
forecast = weather.gridpoints.models.forecast(point.grid_id, point.grid_x, point.grid_y)
for period in forecast.properties.periods:
    print(period.name, period.temperature, period.temperature_unit, period.short_forecast)
hourly = weather.gridpoints.models.forecast_hourly(point.grid_id, point.grid_x, point.grid_y)

latest = weather.stations.models.latest_observation("KMCI").properties
print(latest.temperature.value, latest.temperature.unit_code)  # 23.0 wmoUnit:degC

alerts = weather.alerts.models.active(area=["KS", "MO"])  # a GeoJSON FeatureCollection
for alert in alerts.features:
    print(alert.properties.event, alert.properties.headline)

for observation in weather.stations.models.observations_all("KMCI", limit=50):  # every page
    ...
office = await weather.offices.models.aio.get("TOP")
```

- **Sections:** `alerts`, `points`, `gridpoints`, `stations`, `zones`, `offices`, `products`, `radar`, `radio`, `aviation`, `icons` and `thumbnails`, plus `weather.glossary()`. The spec has no tags, so the sections and method names come from [`specs/weather.names.json`](specs/weather.names.json).
- **Pagination:** `alerts.list_all`, `stations.list_all`, `stations.observations_all` and `zones.stations_all` take the same arguments as their one-page twins and iterate every page's features, following weather.gov's `pagination.next` links. `async for` works through `.aio`, `.pages()` gives whole pages, and `itertools.islice` or `break` stops early. The rules are in [`specs/weather.pagination.yaml`](specs/weather.pagination.yaml).
- **Responses** are GeoJSON (`application/geo+json`), as weather.gov serves by default. The typed models accept enum values the spec doesn't list: a calm hourly period's `wind_direction` is `""`.
- **`points.stations` redirects:** the spec documents only a 301. Use `gridpoints.stations(point.grid_id, point.grid_x, point.grid_y)` instead.

### Aviation weather (AviationWeatherApi)

```python
from noaa_apiroute.aviation import AviationWeatherApi

aviation = AviationWeatherApi(user_agent="myapp (me@example.com)")

[metar] = aviation.models.metar(ids="KMCI", format="json")
print(metar.raw_ob, metar.temp, metar.wdir, metar.wspd)
tafs = aviation.models.taf(ids="KMCI,KSTL", format="json")
pireps = aviation.pirep(id="KMCI", distance=200, format="json")  # dicts: see below
sigmets = aviation.airsigmet(format="json")
```

Every method is on the client: `metar`, `taf`, `pirep`, `airsigmet`, `isigmet`, `sigmet`, `gairmet`, `airmet`, `tcf`, `cwa`, `wind_temp`, `area_forecast`, `forecast_discussion`, `mis`, `station_info`, `airport`, `navaid`, `fix`, `feature`, `obstacle` and `data_server`.
- **Pass `format="json"`.** The API's other formats (`raw`, `xml`, `geojson` ...) aren't JSON.
- **Use the dict layer for `pirep` and `airport`.** Their typed models don't match what the API sends: the spec declares PIREP flight levels and airport coordinates as strings, but they arrive as numbers.

### Rivers and floods (WaterApi)

```python
from noaa_apiroute.water import WaterApi

water = WaterApi(user_agent="myapp (me@example.com)")

gauge = water.gauges.models.get("PTTP1")  # Ohio River at Pittsburgh
print(gauge.name, gauge.status.observed.primary, gauge.status.observed.primary_unit)
observed = water.gauges.models.stage_flow_product("PTTP1", "observed")
nearby = water.gauges.list(bbox_xmin=-80.1, bbox_ymin=40.3, bbox_xmax=-79.9, bbox_ymax=40.5)
streamflow = water.reaches.models.streamflow("3764264")
```

Sections: `gauges` (`list`, `get`, `ratings`, `river_flow`, `stage_flow`, `stage_flow_product`, `river_at_a_glance`), `reaches` (`get`, `streamflow`), `products` and `health`.

### Identifying yourself

NOAA's APIs need no key. But api.weather.gov refuses requests without a `User-Agent`, and asks for one that names your application and gives a contact, so that NWS can reach you about a problem instead of blocking you. See the [NWS API documentation](https://www.weather.gov/documentation/services-web-api) and its [FAQ](https://weather-gov.github.io/api/general-faqs).

| Argument | |
| --- | --- |
| `user_agent` | Sent as `User-Agent` by every client. Defaults to `noaa-apiroute (https://github.com/dougyouch/noaa-apiroute)`; set your own, such as `"myapp (me@example.com)"`. |
| `api_key` | Sent as weather.gov's `API-Key` header. The spec allows it and NWS may require it in the future; it isn't needed today. |
| `base_url` | Another host, such as a proxy. |

Errors raise `apiroute.UnexpectedResponse`. Its `.response` carries NOAA's problem details: `error.response.json()["detail"]`. Retries are off unless you turn them on, for example with `weather.with_options(retries=3)`. For transports, timeouts and other client options, see [apiroute's README](https://github.com/dougyouch/apiroute#readme).

## APIs

<!-- apis:start -->
| API | Import | Docs |
| --- | --- | --- |
| National Weather Service API (api.weather.gov) | `from noaa_apiroute.weather import WeatherApi` | [docs](https://www.weather.gov/documentation/services-web-api) |
| AviationWeather.gov Data API | `from noaa_apiroute.aviation import AviationWeatherApi` | [docs](https://aviationweather.gov/data/api/) |
| National Water Prediction Service API | `from noaa_apiroute.water import WaterApi` | [docs](https://api.water.noaa.gov/nwps/v1/docs/) |
<!-- apis:end -->

Other NOAA services publish no OpenAPI spec, so they aren't generated here. These include Tides and Currents, NCEI's Climate Data Online and the Space Weather Prediction Center.

## How this repository stays up to date

Nothing under `src/noaa_apiroute/` is written by hand except `auth.py` and `__init__.py`. Everything else is generated from the specs listed in [`apis.yaml`](apis.yaml):

1. Every Monday, the **[Build](.github/workflows/build.yml)** workflow does the following:
   - Upgrades apiroute to its newest release.
   - Downloads NOAA's specs into [`specs/`](specs).
   - Regenerates the clients with `apiroute generate`, applying the name maps (`specs/*.names.json`) and the pagination rules in `specs/`.
   - Runs the lint and tests, then the live tests against NOAA's APIs.
2. If anything changed, it commits the result to `main`:
   - `feat(specs): ...` when NOAA changed a spec, which produces a minor release.
   - `fix(codegen): ...` when only a newer apiroute changed the generated code, which produces a patch release.
3. **[Release](.github/workflows/release.yml)** then tests the commit and adds it to [CHANGELOG.md](CHANGELOG.md). It tags the commit, publishes the new version to [PyPI](https://pypi.org/project/noaa-apiroute/) and creates a [GitHub release](https://github.com/dougyouch/noaa-apiroute/releases). No one has to do anything; every merge to main releases the same way.

[CI](.github/workflows/ci.yml) checks every pull request and every release. It lints, runs the tests on Python 3.10 to 3.14, and regenerates from the committed specs to confirm the committed code matches them exactly.

Because `specs/` is committed, `git log -p specs/` shows exactly what NOAA changed and when.

## Development

```bash
uv sync
uv run python scripts/generate.py --fetch   # download the latest specs, regenerate
uv run python scripts/generate.py           # regenerate from the committed specs
uv run python scripts/generate.py --only weather
uv run pytest
NOAA_LIVE=1 uv run pytest tests/live        # against NOAA's APIs
uv run ruff check . && uv run ruff format --check .
```

To add an API:
1. Add an entry to `apis.yaml` with its spec URL, docs URL, module, client class and `base_class: noaa_apiroute.auth:NoaaAuth`.
2. Run `scripts/generate.py --fetch --only <name>`.
3. Add a live test, and commit with `feat:`.

## License

MIT
