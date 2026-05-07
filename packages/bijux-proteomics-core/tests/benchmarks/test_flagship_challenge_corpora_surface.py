# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_challenge_corpora import (
    ChallengeKind,
    HoldoutOutcomeState,
    build_blinded_holdout_reports,
    build_flagship_challenge_registry,
    flagship_challenge_registry_path,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_blinded_holdout_reports_cover_four_flagship_families() -> None:
    reports = {report.workflow_family: report for report in build_blinded_holdout_reports()}

    assert tuple(reports) == ("dda", "dia", "lfq", "ptm")
    assert all(report.withheld_truth_count >= 2 for report in reports.values())
    assert all(report.frozen_surface_paths for report in reports.values())
    assert all(
        any(finding.revealed_outcome is HoldoutOutcomeState.HIT for finding in report.findings)
        for report in reports.values()
    )
    assert all(
        any(
            finding.revealed_outcome is HoldoutOutcomeState.OVERCONFIDENT
            for finding in report.findings
        )
        for report in reports.values()
    )


def test_flagship_challenge_registry_tracks_product_owned_holdout_roots() -> None:
    registry = build_flagship_challenge_registry()

    assert registry.artifact_path == flagship_challenge_registry_path()
    assert len(registry.entries) == 4
    assert all(entry.challenge_kind is ChallengeKind.BLINDED_HOLDOUT for entry in registry.entries)
    for entry in registry.entries:
        assert entry.challenge_root.startswith(
            "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        )


def test_written_holdout_assets_exist_under_challenge_roots() -> None:
    registry = build_flagship_challenge_registry()

    for entry in registry.entries:
        assert (REPO_ROOT / entry.manifest_path).exists()
        assert (REPO_ROOT / entry.report_path).exists()
        assert (REPO_ROOT / entry.challenge_root / "README.md").exists()
