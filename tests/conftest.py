import httpx
import pytest
from apiroute import HttpxClientTransport


class Recorder:
    """A MockTransport handler that records requests and answers with queued responses, or
    raises a queued exception (httpx.ReadTimeout)."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self._responses: list[httpx.Response | Exception] = []

    def respond(self, *responses: httpx.Response | Exception) -> None:
        self._responses.extend(responses)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        response = self._responses.pop(0) if self._responses else httpx.Response(200, json={})
        if isinstance(response, Exception):
            raise response
        return response

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
def transport(recorder) -> HttpxClientTransport:
    return HttpxClientTransport(httpx.Client(transport=httpx.MockTransport(recorder)))
