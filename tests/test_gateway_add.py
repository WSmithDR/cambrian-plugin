import json

import pytest

from lib import gateway, paths


def test_add_idea_creates_jsonl_line():
    idea_id = gateway.add_idea("Docker", "minimalista", "Un solo contenedor sin orquestador")
    assert isinstance(idea_id, str) and len(idea_id) == 8

    f = paths.corpus_file("docker")
    assert f.exists()
    lines = f.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    rec = json.loads(lines[0])
    assert rec["type"] == "idea"
    assert rec["topic"] == "Docker"
    assert rec["lens"] == "minimalista"
    assert rec["text"] == "Un solo contenedor sin orquestador"
    assert rec["status"] == "generada"
    assert rec["id"] == idea_id
    assert rec["ts"]


def test_add_idea_default_status_is_generada():
    gateway.add_idea("Docker", "contrarian", "No uses Docker")
    rec = json.loads(paths.corpus_file("docker").read_text(encoding="utf-8").splitlines()[0])
    assert rec["status"] == "generada"


def test_add_idea_rejects_unknown_status():
    with pytest.raises(ValueError, match="unknown status"):
        gateway.add_idea("Docker", "minimalista", "x", status="inventado")


def test_add_idea_rejects_empty_lens():
    with pytest.raises(ValueError, match="lens"):
        gateway.add_idea("Docker", "", "x")


def test_add_idea_is_append_only():
    gateway.add_idea("Docker", "minimalista", "idea uno")
    gateway.add_idea("Docker", "maximalista", "idea dos")
    lines = paths.corpus_file("docker").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_same_content_yields_same_id():
    a = gateway.add_idea("Docker", "minimalista", "misma idea")
    b = gateway.add_idea("Docker", "minimalista", "misma idea")
    assert a == b
