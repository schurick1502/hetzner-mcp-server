import json
import pytest
from pathlib import Path
from ops.onboard_lib import (
    OnboardError, validate_slug, build_entry, merge_monitor_servers, update_env_file,
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


def _write(tmp_path, body):
    p = tmp_path / ".env"
    p.write_text(body, encoding="utf-8")
    return p


BASE_ENV = (
    "HCLOUD_TOKEN=abc\n"
    'DOCKER_MONITOR_SERVERS=[{"name":"main","host":"10.0.0.1","user":"root","port":22,"aliases":[]}]\n'
)


def test_update_env_adds_token_and_monitor(tmp_path):
    p = _write(tmp_path, BASE_ENV)
    info = update_env_file(str(p), "acme", "TOK123", build_entry("acme", "100.0.0.2", alias="9.9.9.9"))
    text = p.read_text(encoding="utf-8")
    assert "HCLOUD_TOKEN_ACME=TOK123" in text
    assert '"name": "acme"' in text.replace(" ", " ")  # Eintrag vorhanden
    assert info["token_key"] == "HCLOUD_TOKEN_ACME"
    # Backup wurde angelegt und enthält den Originalinhalt
    assert (tmp_path / ".env.bak").read_text(encoding="utf-8") == BASE_ENV


def test_update_env_duplicate_token_without_update_raises(tmp_path):
    p = _write(tmp_path, BASE_ENV + "HCLOUD_TOKEN_ACME=old\n")
    with pytest.raises(OnboardError):
        update_env_file(str(p), "acme", "TOK123", build_entry("acme", "100.0.0.2"))


def test_update_env_update_replaces_token(tmp_path):
    p = _write(tmp_path, BASE_ENV + "HCLOUD_TOKEN_ACME=old\n")
    update_env_file(str(p), "acme", "NEW", build_entry("acme", "100.0.0.2"), allow_update=True)
    text = p.read_text(encoding="utf-8")
    assert "HCLOUD_TOKEN_ACME=NEW" in text and "HCLOUD_TOKEN_ACME=old" not in text
