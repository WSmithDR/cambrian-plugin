import json
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin" / "cambrian"


def _run(args):
    return subprocess.run(
        [sys.executable, str(BIN), *args],
        capture_output=True,
        text=True,
    )


def test_lenses_outputs_six_lenses_json():
    r = _run(["lenses"])
    assert r.returncode == 0
    lenses = json.loads(r.stdout)
    assert len(lenses) == 6
    names = [l["name"] for l in lenses]
    assert "minimalista" in names
    assert "restriccion-absurda" in names
    for l in lenses:
        assert l["name"]
        assert l["mandate"].strip()
