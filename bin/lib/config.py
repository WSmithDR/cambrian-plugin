"""
cambrian-plugin config reader.
Lee config/*.json del repo (PLUGIN_ROOT/config), no del data dir.
Comportamiento externalizado: lentes, umbrales y vocabulario se editan en JSON.
"""

import json

from .paths import PLUGIN_ROOT


def _config_dir():
    return PLUGIN_ROOT / "config"


def load(name: str) -> dict:
    return json.loads((_config_dir() / name).read_text(encoding="utf-8"))


def lenses() -> list:
    return load("lenses.json")["lenses"]


def thresholds() -> dict:
    return load("thresholds.json")


def vocabulary() -> dict:
    return load("vocabulary.json")


def statuses() -> list:
    return vocabulary()["statuses"]
