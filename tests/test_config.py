from lib import config


def test_statuses():
    assert config.statuses() == ["generada", "aceptada", "rechazada"]


def test_lenses_has_six():
    lenses = config.lenses()
    assert len(lenses) == 6
    names = [l["name"] for l in lenses]
    assert "minimalista" in names
    assert "restriccion-absurda" in names
    for l in lenses:
        assert l["mandate"].strip()


def test_thresholds():
    t = config.thresholds()
    assert t["ideas_per_lens"] == 5
    assert t["anti_repetition_window"] == 200
