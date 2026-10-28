"""The identification every generated NOAA client sends.

This file is written by hand: the generated clients extend NoaaAuth (through the `base_class`
entries in apis.yaml), so regenerating never touches it.
"""

from typing import Any

from apiroute import Client, RequestSpec

DEFAULT_USER_AGENT = "noaa-apiroute (https://github.com/dougyouch/noaa-apiroute)"

# Operations sent as POST that only read, so they're as safe to retry as a GET
READ_ONLY_POSTS = frozenset({"Gauges_GetRiverAtAGlanceData"})


class NoaaAuth(Client):
    """A User-Agent naming your application, and weather.gov's optional API key.

        weather = WeatherApi(user_agent="myapp (me@example.com)")
        weather.points.get(latitude=39.7456, longitude=-97.0892)

    NOAA's APIs need no key, but api.weather.gov refuses requests without a User-Agent and
    asks for one that identifies the application and a way to contact its author, so that it
    can reach you about a problem rather than block you. user_agent defaults to this package's
    name; set your own. api_key is sent as weather.gov's API-Key header, which NWS may require
    in the future.
    """

    headers = {
        "User-Agent": lambda self: self.user_agent,
        "API-Key": lambda self: self.api_key,
    }

    def __init__(
        self,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        api_key: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.user_agent = user_agent
        self.api_key = api_key

    def idempotent(self, request: RequestSpec) -> bool | None:
        return True if request.operation in READ_ONLY_POSTS else None
