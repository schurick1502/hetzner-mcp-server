import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE_ENV = (
    "HCLOUD_TOKEN=abc\n"
    'DOCKER_MONITOR_SERVERS=[{"name":"main","host":"10.0.0.1","user":"root","port":22,"aliases":[]}]\n'
)


def _run(args, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run([sys.executable, "-m", "ops.onboard_lib", *args],
                          cwd=REPO, env=env, capture_output=True, text=True)


def test_cli_dry_run_does_not_write(tmp_path):
    p = tmp_path / ".env"; p.write_text(BASE_ENV, encoding="utf-8")
    r = _run(["update-env", "--env-file", str(p), "--slug", "acme",
              "--host", "100.0.0.2", "--dry-run"],
             {"ONBOARD_TOKEN": "TOK"})
    assert r.returncode == 0, r.stderr
    assert p.read_text(encoding="utf-8") == BASE_ENV  # unverändert
    assert "acme" in r.stdout


def test_cli_writes_and_is_idempotent(tmp_path):
    p = tmp_path / ".env"; p.write_text(BASE_ENV, encoding="utf-8")
    r1 = _run(["update-env", "--env-file", str(p), "--slug", "acme",
               "--host", "100.0.0.2"], {"ONBOARD_TOKEN": "TOK"})
    assert r1.returncode == 0, r1.stderr
    assert "HCLOUD_TOKEN_ACME=TOK" in p.read_text(encoding="utf-8")
    # Zweiter Lauf ohne --update -> Exit 2, Token bleibt in Ausgabe unsichtbar
    r2 = _run(["update-env", "--env-file", str(p), "--slug", "acme",
               "--host", "100.0.0.2"], {"ONBOARD_TOKEN": "TOK"})
    assert r2.returncode == 2
    assert "TOK" not in (r2.stdout + r2.stderr)
