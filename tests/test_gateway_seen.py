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
    # implementation keeps the FIRST occurrence's original text (tie-break pinned)
    assert seen == ["Idea Repetida"]


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


def test_seen_dedup_and_limit_interact():
    """FIX 4: dedup happens before limit; result is post-dedup unique texts, most-recent N."""
    # Add ideas: "alpha" appears twice (normalized), "beta", "gamma", "delta" once each.
    # Insertion order: alpha_v1, alpha_v2, beta, gamma, delta
    # After dedup (keep first occurrence): alpha_v1, beta, gamma, delta  (4 unique)
    # With limit=3: keep last 3 → [beta, gamma, delta]
    gateway.add_idea("Docker", "minimalista", "Alpha")
    gateway.add_idea("Docker", "maximalista", "alpha")   # duplicate of "Alpha" (normalized)
    gateway.add_idea("Docker", "contrarian", "beta")
    gateway.add_idea("Docker", "minimalista", "gamma")
    gateway.add_idea("Docker", "maximalista", "delta")
    seen = gateway.seen_texts("Docker", limit=3)
    assert seen == ["beta", "gamma", "delta"]
