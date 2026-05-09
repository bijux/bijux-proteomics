from __future__ import annotations

from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    build_benchmark_comparability_matrix,
    build_benchmark_rerun_kits,
    run,
)


def test_benchmark_rerun_governance_pages_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_benchmark_rerun_kits_cover_all_workflow_families() -> None:
    kits = build_benchmark_rerun_kits()

    assert len(kits) == 6
    assert {entry.workflow_family.value for entry in kits} == {
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    }
    assert all(entry.primary_spec.canonical_entrypoint for entry in kits)
    assert all(entry.companion_spec.canonical_entrypoint for entry in kits)
    assert all(entry.validating_test_paths for entry in kits)
    multiplex = next(entry for entry in kits if entry.workflow_family.value == "multiplex")
    assert multiplex.independent_rerun_path is None
    assert multiplex.external_review_kit_path is None
    assert "internal-support only" in " ".join(multiplex.remaining_limits)


def test_benchmark_comparability_matrix_keeps_cross_package_drift_visible() -> None:
    rows = build_benchmark_comparability_matrix()

    assert len(rows) == 6
    assert all(row.report_path.endswith("cross_package_generalization.json") for row in rows)
    assert all(row.surviving_claim_count + row.weakened_claim_count + row.collapsed_claim_count > 0 for row in rows)
    assert any(row.collapsed_claim_count > 0 for row in rows)
