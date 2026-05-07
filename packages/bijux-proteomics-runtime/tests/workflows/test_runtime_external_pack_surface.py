# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows.assurance import workflow_assurance_lanes


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def test_runtime_assurance_keeps_maxquant_search_pack_visible() -> None:
    repo_root = _repo_root()
    lane = next(
        lane for lane in workflow_assurance_lanes() if lane.lane_id == "dda-maxquant-compatibility-pack"
    )

    assert lane.workflow_family == "dda_import"
    assert any(path.endswith("maxquant_evidence.tsv") for path in lane.repo_relative_fixture_paths)
    assert any(path.endswith("maxquant_pipeline_export.tsv") for path in lane.repo_relative_fixture_paths)
    assert all((repo_root / path).exists() for path in lane.repo_relative_fixture_paths)


def test_runtime_assurance_keeps_diann_quant_pack_visible() -> None:
    repo_root = _repo_root()
    lane = next(
        lane for lane in workflow_assurance_lanes() if lane.lane_id == "dia-diann-compatibility-pack"
    )

    assert lane.workflow_family == "dia_import"
    assert any(path.endswith("diann_report.tsv") for path in lane.repo_relative_fixture_paths)
    assert any(path.endswith("diann_pipeline_export.tsv") for path in lane.repo_relative_fixture_paths)
    assert any(path.endswith("diann_config.json") for path in lane.repo_relative_fixture_paths)
    assert all((repo_root / path).exists() for path in lane.repo_relative_fixture_paths)


def test_runtime_ptm_review_corpus_remains_tracked() -> None:
    repo_root = _repo_root()

    assert (
        repo_root
        / "packages/bijux-proteomics-runtime/tests/fixtures/ptm/localization_results.tsv"
    ).exists()
    assert (
        repo_root / "packages/bijux-proteomics-runtime/tests/fixtures/ptm/ptm_features.tsv"
    ).exists()
