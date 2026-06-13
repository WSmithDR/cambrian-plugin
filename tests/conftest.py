import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))


@pytest.fixture(autouse=True)
def _data_dir(tmp_path, monkeypatch):
    """Redirige CAMBRIAN_DATA_DIR a un tmp por test. Nunca toca el real."""
    monkeypatch.setenv("CAMBRIAN_DATA_DIR", str(tmp_path))
    yield
