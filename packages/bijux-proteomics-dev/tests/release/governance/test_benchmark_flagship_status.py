from __future__ import annotations

from bijux_proteomics_dev.release.governance.benchmark_flagship_status import (
    build_benchmark_flagship_status,
    run,
    validate_benchmark_flagship_promotion,
)


def test_benchmark_flagship_status_page_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_benchmark_flagship_status_demotes_companions_and_keeps_multiplex_internal() -> (
    None
):
    entries = build_benchmark_flagship_status()

    assert len(entries) == 12
    assert validate_benchmark_flagship_promotion() == ()
    assert (
        sum(entry.designation == "generalization_companion" for entry in entries) == 6
    )
    multiplex_primary = next(
        entry
        for entry in entries
        if entry.workflow_family.value == "multiplex"
        and entry.package_role == "primary flagship package"
    )
    assert multiplex_primary.designation == "flagship_primary_internal_support"
    assert multiplex_primary.eligible_for_designation is True
    assert all(
        entry.eligible_for_designation
        for entry in entries
        if entry.designation.startswith("flagship_")
    )
