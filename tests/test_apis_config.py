"""Every API in apis.yaml is fetched, generated and importable, and every route compiles."""

import importlib
import json
from pathlib import Path

import pytest
import yaml
from apiroute.lazy_attribute import LazyAttribute
from apiroute.route_method import RouteMethod

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "apis.yaml").read_text())
APIS = CONFIG["apis"]


def test_names_and_modules_are_unique():
    assert len({api["name"] for api in APIS}) == len(APIS)
    assert len({api["module"] for api in APIS}) == len(APIS)


@pytest.mark.parametrize("api", APIS, ids=lambda api: api["name"])
def test_each_api(api):
    specs = ROOT / "specs"
    assert any((specs / f"{api['name']}{suffix}").is_file() for suffix in (".json", ".yaml"))
    assert api["docs"].startswith("https://")
    for option in ("operation_names", "pagination"):
        if api.get(option):
            assert (ROOT / api[option]).is_file()
    module = importlib.import_module(f"{CONFIG['package']}.{api['module']}")
    client = getattr(module, api["client"])
    base_module, base_name = api["base_class"].split(":")
    assert issubclass(client, getattr(importlib.import_module(base_module), base_name))
    assert client._config.base_url.startswith("https://")
    assert _compile_routes(client) > 0


@pytest.mark.parametrize(
    "api", [api for api in APIS if api.get("operation_names")], ids=lambda api: api["name"]
)
def test_every_name_is_a_dotted_python_name(api):
    names = json.loads((ROOT / api["operation_names"]).read_text())
    assert names and all(part.isidentifier() for name in names.values() for part in name.split("."))


def _compile_routes(router_class: type) -> int:
    """Compiles every route of a client and its sections; returns how many there were."""
    count = 0
    for name, value in vars(router_class).items():
        if isinstance(value, RouteMethod):
            assert value.definition.name == name
            count += 1
        elif isinstance(value, LazyAttribute) and name != "models":
            count += _compile_routes(value.load())
    return count
