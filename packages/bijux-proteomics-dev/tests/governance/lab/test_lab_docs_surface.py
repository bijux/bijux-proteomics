from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
LAB_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-lab"


def _combined_docs() -> str:
    parts = [
        (LAB_ROOT / "README.md").read_text(encoding="utf-8"),
        (LAB_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
        (LAB_ROOT / "docs" / "BOUNDARIES.md").read_text(encoding="utf-8"),
        (LAB_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8"),
    ]
    return "\n".join(parts)


def test_lab_docs_publish_execution_reality_and_owner_families() -> None:
    text = _combined_docs()
    lowered = text.lower()

    assert "operational honesty, feasibility, and traceability" in lowered
    assert "queue pressure" in lowered
    assert "material limits" in lowered
    assert "handoff honesty" in lowered
    assert "planning/assays.py" in text
    assert "planning/scheduling.py" in text
    assert "planning/priorities.py" in text
    assert "planning/next_cycle.py" in text
    assert "handoffs/transitions.py" in text
    assert "handoffs/explanations.py" in text
    assert "handoffs/exports.py" in text
    assert "reconciliation/follow_up.py" in text
    assert "benchmarks/rehearsals.py" in text
    assert "benchmarks/outcome_dossiers.py" in text


def test_lab_docs_keep_non_goals_and_refusal_behavior_explicit() -> None:
    text = _combined_docs().lower()

    assert "analytical recommendation logic" in text
    assert "core scientific semantics" in text
    assert "execution orchestration or runtime policy" in text
    assert "refusal behavior" in text
    assert "lossy export notes" in text
    assert "handoffs/packets.py" not in text
    assert "benchmarks/targeted.py" not in text
    assert "readiness/workflow.py" not in text
