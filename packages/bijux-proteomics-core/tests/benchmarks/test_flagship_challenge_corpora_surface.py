# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_challenge_corpora import (
    ChallengeKind,
    HoldoutOutcomeState,
    build_blinded_holdout_reports,
    build_flagship_challenge_registry,
    build_perturbation_reports,
    flagship_challenge_registry_path,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_blinded_holdout_reports_cover_four_flagship_families() -> None:
    reports = {
        report.workflow_family: report for report in build_blinded_holdout_reports()
    }

    assert tuple(reports) == ("dda", "dia", "lfq", "ptm")
    assert all(report.withheld_truth_count >= 2 for report in reports.values())
    assert all(report.frozen_surface_paths for report in reports.values())
    assert all(
        any(
            finding.revealed_outcome is HoldoutOutcomeState.HIT
            for finding in report.findings
        )
        for report in reports.values()
    )
    assert all(
        any(
            finding.revealed_outcome is HoldoutOutcomeState.OVERCONFIDENT
            for finding in report.findings
        )
        for report in reports.values()
    )


def test_first_perturbation_reports_publish_measured_reaction_states() -> None:
    reports = {
        report.workflow_family: report for report in build_perturbation_reports()
    }

    assert tuple(reports) == ("dda", "dia", "lfq", "multiplex", "ptm", "targeted")
    assert reports["dda"].workflow_reaction.value == "collapses"
    assert reports["dia"].comparator_reaction.value in {"weakens", "collapses"}
    assert reports["lfq"].metric_deltas
    assert reports["multiplex"].review_reaction.value == "collapses"
    assert reports["ptm"].workflow_reaction.value == "weakens"
    assert reports["targeted"].review_reaction.value == "collapses"
    assert all(report.perturbation_axes for report in reports.values())
    assert all(report.evidence_paths for report in reports.values())


def test_flagship_challenge_registry_tracks_product_owned_challenge_roots() -> None:
    registry = build_flagship_challenge_registry()

    assert registry.artifact_path == flagship_challenge_registry_path()
    assert len(registry.entries) == 10
    assert (
        sum(
            entry.challenge_kind is ChallengeKind.BLINDED_HOLDOUT
            for entry in registry.entries
        )
        == 4
    )
    assert (
        sum(
            entry.challenge_kind is ChallengeKind.PERTURBATION
            for entry in registry.entries
        )
        == 6
    )
    for entry in registry.entries:
        assert entry.challenge_root.startswith(
            "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        )


def test_written_challenge_assets_exist_under_challenge_roots() -> None:
    registry = build_flagship_challenge_registry()

    for entry in registry.entries:
        assert (REPO_ROOT / entry.manifest_path).exists()
        assert (REPO_ROOT / entry.report_path).exists()
        assert (REPO_ROOT / entry.challenge_root / "README.md").exists()
