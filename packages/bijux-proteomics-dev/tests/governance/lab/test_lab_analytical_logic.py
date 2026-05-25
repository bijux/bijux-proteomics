from __future__ import annotations

from bijux_proteomics_dev.governance.lab.analytical_logic import (
    ALLOWED_ANALYTICAL_MODULES,
    LAB_ANALYTICAL_LOGIC_PATH,
    build_lab_analytical_logic_report,
    run,
    validate_lab_analytical_logic,
)


def test_lab_analytical_logic_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_analytical_logic_stays_in_governed_operational_hotspots() -> None:
    report = build_lab_analytical_logic_report()

    assert LAB_ANALYTICAL_LOGIC_PATH.exists()
    assert tuple(module.module_path for module in report) == ALLOWED_ANALYTICAL_MODULES
    assert any(
        identifier == "candidate_assessments"
        for module in report
        if module.module_path == "benchmarks/claims.py"
        for identifier in module.matched_identifiers
    )
    assert any(
        identifier == "contradiction_pressure"
        for module in report
        if module.module_path == "planning/next_cycle.py"
        for identifier in module.matched_identifiers
    )
    assert any(
        identifier == "skeptical_candidate_ids"
        for module in report
        if module.module_path == "planning/priorities.py"
        for identifier in module.matched_identifiers
    )


def test_lab_analytical_logic_release_guard_has_no_failures() -> None:
    assert validate_lab_analytical_logic() == ()
