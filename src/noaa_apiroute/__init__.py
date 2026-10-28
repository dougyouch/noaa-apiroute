"""Python clients for NOAA's weather APIs, generated with apiroute from their OpenAPI specs.

    from noaa_apiroute.weather import WeatherApi

    weather = WeatherApi(user_agent="myapp (me@example.com)")
    point = weather.points.models.get(latitude=39.7456, longitude=-97.0892).properties
    forecast = weather.gridpoints.models.forecast(point.grid_id, point.grid_x, point.grid_y)

Only noaa_apiroute.auth (the hand-written NoaaAuth) and this file are written by hand;
noaa_apiroute.weather, .aviation and .water are regenerated from NOAA's specs.
"""
