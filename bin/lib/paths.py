"""
cambrian-plugin path resolution.
Toda la persistencia resuelve contra CAMBRIAN_DATA_DIR (~/.local/share/cambrian).
Las funciones leen el env en CALL-TIME (no import-time) para que los tests
puedan redirigir el data dir sin tocar el real.
"""

import os
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return Path(
        os.environ.get(
            "CAMBRIAN_DATA_DIR", Path.home() / ".local" / "share" / "cambrian"
        )
    )


def corpus_dir() -> Path:
    return data_dir() / "corpus"


def corpus_file(topic_slug: str) -> Path:
    return corpus_dir() / f"{topic_slug}.jsonl"


def slugify(topic: str) -> str:
    s = topic.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"
