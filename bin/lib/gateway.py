"""
cambrian-plugin corpus gateway.
El corpus es append-only: un JSONL por topic en $CAMBRIAN_DATA_DIR/corpus/.
Records de tipo 'idea' y 'status'; el status vigente se foldea al leer.
Las skills NUNCA escriben disco directo: pasan por bin/cambrian, que llama acá.
"""

import hashlib
import json
import time

from . import config
from .paths import corpus_dir, corpus_file, slugify


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gen_id(topic: str, lens: str, text: str) -> str:
    h = hashlib.sha256(f"{topic}|{lens}|{text}".encode("utf-8")).hexdigest()
    return h[:8]


def _validate_status(status: str) -> None:
    valid = config.statuses()
    if status not in valid:
        raise ValueError(f"unknown status '{status}'; valid: {valid}")


def _append(topic: str, rec: dict) -> None:
    corpus_dir().mkdir(parents=True, exist_ok=True)
    with corpus_file(slugify(topic)).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def add_idea(topic: str, lens: str, text: str, status: str = "generada") -> str:
    if not lens or not lens.strip():
        raise ValueError("lens must be a non-empty string")
    _validate_status(status)
    idea_id = _gen_id(topic, lens, text)
    _append(
        topic,
        {
            "id": idea_id,
            "type": "idea",
            "topic": topic,
            "lens": lens,
            "text": text,
            "status": status,
            "ts": _now(),
        },
    )
    return idea_id


def mark(topic: str, idea_id: str, status: str) -> None:
    _validate_status(status)
    _append(topic, {"type": "status", "id": idea_id, "status": status, "ts": _now()})


def _read_records(topic: str) -> list:
    f = corpus_file(slugify(topic))
    if not f.exists():
        return []
    records = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def list_ideas(topic: str) -> list:
    records = _read_records(topic)
    ideas = {}
    order = []
    for r in records:
        if r.get("type") == "idea":
            if r["id"] not in ideas:
                order.append(r["id"])
            ideas[r["id"]] = dict(r)
    for r in records:
        if r.get("type") == "status" and r["id"] in ideas:
            ideas[r["id"]]["status"] = r["status"]
    return [ideas[i] for i in order]
