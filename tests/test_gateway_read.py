import pytest

from lib import gateway, paths


def test_list_empty_topic_returns_empty():
    assert gateway.list_ideas("inexistente") == []


def test_list_returns_ideas_in_order():
    gateway.add_idea("Docker", "minimalista", "primera")
    gateway.add_idea("Docker", "maximalista", "segunda")
    ideas = gateway.list_ideas("Docker")
    assert [i["text"] for i in ideas] == ["primera", "segunda"]


def test_mark_updates_status_via_fold():
    idea_id = gateway.add_idea("Docker", "minimalista", "candidata")
    gateway.mark("Docker", idea_id, "aceptada")
    ideas = gateway.list_ideas("Docker")
    assert len(ideas) == 1
    assert ideas[0]["status"] == "aceptada"


def test_latest_status_wins():
    idea_id = gateway.add_idea("Docker", "minimalista", "candidata")
    gateway.mark("Docker", idea_id, "aceptada")
    gateway.mark("Docker", idea_id, "rechazada")
    ideas = gateway.list_ideas("Docker")
    assert ideas[0]["status"] == "rechazada"


def test_mark_rejects_unknown_status():
    idea_id = gateway.add_idea("Docker", "minimalista", "x")
    with pytest.raises(ValueError, match="unknown status"):
        gateway.mark("Docker", idea_id, "inventado")


def test_mark_unknown_id_is_ignored_on_read():
    gateway.add_idea("Docker", "minimalista", "real")
    gateway.mark("Docker", "ffffffff", "aceptada")
    ideas = gateway.list_ideas("Docker")
    assert len(ideas) == 1
    assert ideas[0]["status"] == "generada"


def test_list_skips_malformed_jsonl_lines():
    """FIX 1: malformed lines in JSONL must be skipped, not crash the read."""
    from lib.paths import corpus_file, slugify

    gateway.add_idea("Docker", "minimalista", "idea valida")
    # Manually corrupt the file by appending a garbage line
    corrupt_file = corpus_file(slugify("Docker"))
    with corrupt_file.open("a", encoding="utf-8") as fh:
        fh.write("not json{\n")
    # list_ideas must still return the valid idea without raising
    ideas = gateway.list_ideas("Docker")
    assert len(ideas) == 1
    assert ideas[0]["text"] == "idea valida"
