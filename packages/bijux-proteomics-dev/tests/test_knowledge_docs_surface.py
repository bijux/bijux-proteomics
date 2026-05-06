from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-knowledge"


def _combined_docs() -> str:
    parts = [
        (KNOWLEDGE_ROOT / "README.md").read_text(encoding="utf-8"),
        (KNOWLEDGE_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
        (KNOWLEDGE_ROOT / "docs" / "BOUNDARIES.md").read_text(encoding="utf-8"),
        (KNOWLEDGE_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8"),
    ]
    return "\n".join(parts)


def test_knowledge_docs_publish_scientific_memory_and_owner_families() -> None:
    text = _combined_docs()

    assert "scientific memory with provenance" in text
    assert "memory/models/evidence.py" in text
    assert "memory/models/claims.py" in text
    assert "memory/reconciliation/resolution.py" in text
    assert "reviews/packets.py" in text
    assert "references/grounding/" in text
    assert "references/workflows/" in text
    assert "selective" in text


def test_knowledge_docs_keep_non_goals_explicit_and_credible() -> None:
    text = _combined_docs().lower()

    assert "does not own execution orchestration" in text
    assert "ranking or recommendation policy" in text
    assert "route-shaped payloads" in text
    assert "generic context sink" in text
    assert "reviews/queries.py" not in text
