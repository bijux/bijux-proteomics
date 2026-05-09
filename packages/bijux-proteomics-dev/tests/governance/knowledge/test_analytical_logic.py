from __future__ import annotations

from bijux_proteomics_dev.governance.knowledge.analytical_logic import (
    ALLOWED_ANALYTICAL_MODULES,
    KNOWLEDGE_ANALYTICAL_LOGIC_PATH,
    build_knowledge_analytical_logic_report,
    run,
    validate_knowledge_analytical_logic,
)


def test_knowledge_analytical_logic_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_knowledge_analytical_logic_stays_in_governed_hotspots() -> None:
    report = build_knowledge_analytical_logic_report()

    assert KNOWLEDGE_ANALYTICAL_LOGIC_PATH.exists()
    assert tuple(module.module_path for module in report) == ALLOWED_ANALYTICAL_MODULES
    assert any(
        identifier == "gate_recommendation"
        for module in report
        if module.module_path == "reviews/decision_briefs.py"
        for identifier in module.matched_identifiers
    )
    assert any(
        identifier == "score_evidence_record"
        for module in report
        if module.module_path == "memory/models/evidence.py"
        for identifier in module.matched_identifiers
    )


def test_knowledge_analytical_logic_release_guard_has_no_failures() -> None:
    assert validate_knowledge_analytical_logic() == ()
