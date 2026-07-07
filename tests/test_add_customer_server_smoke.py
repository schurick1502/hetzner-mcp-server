import shutil
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "ops" / "add-customer-server.sh"

# On Windows, a bare "bash" can be hijacked by the WSL App-Execution-Alias
# stub at C:\WINDOWS\system32\bash.exe (present even without WSL installed),
# regardless of PATH order. Resolve the real bash executable explicitly
# (shutil.which correctly finds Git Bash) so the smoke test is reliable
# across dev machines.
BASH = shutil.which("bash") or "bash"


def test_script_exists_and_valid_bash():
    assert SCRIPT.exists()
    r = subprocess.run([BASH, "-n", str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr  # Syntax ok


def test_usage_on_missing_args():
    r = subprocess.run([BASH, str(SCRIPT), "--help"], capture_output=True, text=True)
    assert "add-customer-server.sh" in (r.stdout + r.stderr)
    assert "--slug" in (r.stdout + r.stderr)
