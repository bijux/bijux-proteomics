# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.dda_reviewable_package import (
    build_dda_reviewable_package,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def test_dda_reviewable_package_keeps_real_artifacts_visible() -> None:
    repo_root = _repo_root()
    package = build_dda_reviewable_package()

    assert package.package_id == "public_benchmark_package:dda_reviewable_run"
    assert package.runtime_package_id == "dda-maxquant-pipeline-corpus"
    assert package.comparator_path_ids == ("comparator_path:msfragger_imported_dda_review",)
    assert all((repo_root / path).exists() for path in package.public_package_files)
    assert all((repo_root / artifact.repo_relative_path).exists() for artifact in package.artifacts)
    assert any(
        artifact.repo_relative_path.endswith("maxquant_pipeline_export.tsv")
        for artifact in package.artifacts
    )
    assert any(
        artifact.repo_relative_path.endswith("msfragger_pipeline_export.tsv")
        for artifact in package.artifacts
    )


def test_dda_reviewable_package_tracks_numerical_invariants_from_real_exports() -> None:
    package = build_dda_reviewable_package()
    by_id = {entry.invariant_id: entry for entry in package.scientific_invariants}

    assert by_id["dda_reviewable_run:maxquant_target_psm_count"].observed_numeric == 2.0
    assert by_id["dda_reviewable_run:maxquant_decoy_psm_count"].observed_numeric == 1.0
    assert (
        by_id["dda_reviewable_run:maxquant_observed_q_ceiling"].observed_numeric
        <= by_id["dda_reviewable_run:maxquant_observed_q_ceiling"].expected_numeric
    )
    assert (
        by_id["dda_reviewable_run:adapter_parity_pass_count"].observed_numeric == 2.0
    )
    assert (
        by_id["dda_reviewable_run:identification_loss_free_count"].observed_numeric
        == 2.0
    )


def test_dda_reviewable_package_turns_review_warning_into_public_demonstration() -> None:
    package = build_dda_reviewable_package()

    warning = package.warning_demonstrations[0]

    assert warning.warning_id == "dda_reviewable_run:protein_rollup_engine_drift"
    assert warning.demonstrated_metric == 5.0
    assert "protein-facing dda claims" in warning.consequence.lower()
    assert {
        "dda_reviewable_run:maxquant_export",
        "dda_reviewable_run:msfragger_export",
    } <= set(warning.evidence_artifact_ids)


def test_dda_reviewable_package_keeps_reader_facing_citations_and_runtime_artifacts() -> (
    None
):
    package = build_dda_reviewable_package()

    assert any(
        citation.url == "https://www.nature.com/articles/nmeth1019"
        for citation in package.citation_refs
    )
    assert any(path.endswith("review_packet.json") for path in package.review_artifact_paths)
    assert any(
        path.endswith("test_benchmark_runtime_surface.py")
        for path in package.validating_test_paths
    )
