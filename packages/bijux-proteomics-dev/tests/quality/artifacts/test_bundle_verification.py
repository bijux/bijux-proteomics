from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.artifacts.bundle_verification import (
    load_bundle_verification_profiles,
    validate_bundle_verification_profiles,
    verify_bundle_payload,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_bundle_verification_profiles_cover_curated_bundle_kinds() -> None:
    profiles = load_bundle_verification_profiles(REPO_ROOT)

    assert len(profiles) == 6
    assert {profile.document_kind for profile in profiles} == {
        "evidence_bundle",
        "workflow_runtime_export_bundle",
        "workflow_runtime_archive_bundle",
        "workflow_rerun_comparison_artifact",
        "review_ready_evidence_bundle",
        "quant_artifact_bundle",
    }


def test_bundle_verification_profiles_are_valid_for_current_repo() -> None:
    assert validate_bundle_verification_profiles(REPO_ROOT) == ()


def test_verify_bundle_payload_accepts_matching_runtime_archive_bundle() -> None:
    payload = {
        "document_schema": {
            "document_kind": "workflow_runtime_archive_bundle",
            "schema_version": "1.0.0",
        },
        "workflow_id": "workflow-1",
        "run_id": "run-1",
        "archive_medium": "portable_json",
        "export_bundle_sha256": "a" * 64,
        "archive_bundle_sha256": "b" * 64,
        "archived_artifacts": [],
        "export_bundle": {},
    }

    report = verify_bundle_payload(
        payload,
        document_kind="workflow_runtime_archive_bundle",
        repo_root=REPO_ROOT,
    )

    assert report.valid is True
    assert "archive_bundle_sha256" in report.verified_fields
