from __future__ import annotations

from bijux_proteomics_dev.docs.governance.claim_proof import (
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
    assert report.guard.max_total_unproven_claim_kind_count == 0
    assert entries["bijux-proteomics-dev"].unproven_claim_kinds == ()
    assert entries["bijux-proteomics-knowledge"].unproven_claim_kinds == ()
    assert entries["bijux-proteomics-lab"].unproven_claim_kinds == ()
    assert report.guard.min_total_benchmark_proof_artifact_count == 51
    assert report.guard.min_total_replay_proof_artifact_count == 7
    assert report.guard.min_total_integrity_proof_artifact_count == 5
    assert (
        entries["bijux-proteomics-intelligence"].benchmark_proof_artifacts_per_claim
        < entries["bijux-proteomics-core"].benchmark_proof_artifacts_per_claim
    )
    assert (
        "packages/bijux-proteomics-dev/README.md"
        in entries["bijux-proteomics-dev"].integrity_claim_document_paths
    )
    assert (
        "packages/bijux-proteomics-dev/tests/docs/governance/test_source_path_integrity.py"
        in entries["bijux-proteomics-dev"].integrity_proof_artifact_paths
    )
    assert (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py"
        in entries["bijux-proteomics-knowledge"].replay_proof_artifact_paths
    )


def test_package_docs_claim_proof_release_guard_has_no_failures() -> None:
    assert validate_package_docs_claim_proof() == ()
