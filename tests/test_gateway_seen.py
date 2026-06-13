from lib import gateway


def test_seen_empty_topic():
    assert gateway.seen_texts("inexistente") == []


def test_seen_returns_unique_texts():
    gateway.add_idea("Docker", "minimalista", "idea A")
    gateway.add_idea("Docker", "maximalista", "idea B")
    seen = gateway.seen_texts("Docker")
    assert "idea A" in seen
    assert "idea B" in seen


def test_seen_dedupes_normalized_text():
    gateway.add_idea("Docker", "minimalista", "Idea Repetida")
    gateway.add_idea("Docker", "maximalista", "idea   repetida")
    seen = gateway.seen_texts("Docker")
    assert len(seen) == 1


def test_seen_respects_limit_window():
    for i in range(10):
        gateway.add_idea("Docker", "minimalista", f"idea {i}")
    seen = gateway.seen_texts("Docker", limit=3)
    assert len(seen) == 3
    # devuelve las más recientes
    assert seen == ["idea 7", "idea 8", "idea 9"]


def test_seen_default_limit_from_config():
    # con pocas ideas, el window default (200) no recorta
    gateway.add_idea("Docker", "minimalista", "una")
    assert gateway.seen_texts("Docker") == ["una"]
