from __future__ import annotations

from bijux_proteomics_dev.api.package_docs_claim_proof import (
    PACKAGE_DOCS_CLAIM_PROOF_PATH,
    build_package_docs_claim_proof_report,
    run,
    validate_package_docs_claim_proof,
)


def test_package_docs_claim_proof_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_docs_claim_proof_report_tracks_current_evidence_gaps() -> None:
    report = build_package_docs_claim_proof_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_DOCS_CLAIM_PROOF_PATH.exists()
    assert len(report.entries) == 8
    assert report.guard.max_total_unproven_claim_kind_count == 3
    assert entries["bijux-proteomics-dev"].unproven_claim_kinds == ("integrity",)
    assert entries["bijux-proteomics-knowledge"].unproven_claim_kinds == ("replay",)
    assert entries["bijux-proteomics-lab"].unproven_claim_kinds == ("integrity",)
    assert report.guard.min_total_benchmark_proof_artifact_count == 20


def test_package_docs_claim_proof_release_guard_has_no_failures() -> None:
    assert validate_package_docs_claim_proof() == ()
