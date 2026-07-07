import json
import pytest
from ops.onboard_lib import (
    OnboardError, validate_slug, build_entry, merge_monitor_servers,
)


def test_validate_slug_ok():
    assert validate_slug("Ehmen") == "ehmen"
    assert validate_slug("acme_01") == "acme_01"


@pytest.mark.parametrize("bad", ["tsv-ehmen", "acme server", "", "a.b"])
def test_validate_slug_rejects(bad):
    with pytest.raises(OnboardError):
        validate_slug(bad)


def test_build_entry_defaults_and_alias():
    e = build_entry("acme", "100.0.0.1", alias="1.2.3.4")
    assert e == {"name": "acme", "host": "100.0.0.1", "user": "root",
                 "port": 22, "aliases": ["1.2.3.4"]}
    assert build_entry("acme", "1.1.1.1")["aliases"] == []


def test_merge_appends_new():
    cur = '[{"name":"a","host":"h1","user":"root","port":22,"aliases":[]}]'
    out = json.loads(merge_monitor_servers(cur, build_entry("b", "h2")))
    assert [s["name"] for s in out] == ["a", "b"]


def test_merge_empty_current():
    out = json.loads(merge_monitor_servers("", build_entry("b", "h2")))
    assert out[0]["name"] == "b"


def test_merge_duplicate_without_update_raises():
    cur = '[{"name":"a","host":"h1","user":"root","port":22,"aliases":[]}]'
    with pytest.raises(OnboardError):
        merge_monitor_servers(cur, build_entry("a", "hX"))


def test_merge_duplicate_with_update_replaces():
    cur = '[{"name":"a","host":"h1","user":"root","port":22,"aliases":[]}]'
    out = json.loads(merge_monitor_servers(cur, build_entry("a", "hNEW"), allow_update=True))
    assert len(out) == 1 and out[0]["host"] == "hNEW"
