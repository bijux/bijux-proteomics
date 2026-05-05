from __future__ import annotations

from bijux_proteomics_dev.api.lab_core_scientific_semantics import (
    ALLOWED_SCIENTIFIC_IMPORTS,
    LAB_CORE_SCIENTIFIC_SEMANTICS_PATH,
    build_lab_core_scientific_semantics_report,
    run,
    validate_lab_core_scientific_semantics,
)


def test_lab_core_scientific_semantics_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_core_scientific_semantics_stay_on_governed_operational_edges() -> None:
    report = build_lab_core_scientific_semantics_report()
    observed = tuple(
        (entry.importer_module_path, entry.imported_module_name) for entry in report
    )

    assert LAB_CORE_SCIENTIFIC_SEMANTICS_PATH.exists()
    assert observed == ALLOWED_SCIENTIFIC_IMPORTS
    assert ("handoffs/ptm.py", "bijux_proteomics.ptm.review") in observed
    assert ("benchmarks/claims.py", "bijux_proteomics.dia") in observed


def test_lab_core_scientific_semantics_release_guard_has_no_failures() -> None:
    assert validate_lab_core_scientific_semantics() == ()
