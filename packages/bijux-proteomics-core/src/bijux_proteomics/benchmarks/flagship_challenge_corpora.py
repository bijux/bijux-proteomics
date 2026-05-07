# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship challenge corpora for blinded holdouts and adversarial perturbations."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.workflow_generalization import (
    WorkflowGeneralizationReport,
    build_workflow_generalization_reports,
)
from bijux_proteomics_foundation import JsonModel

_CHALLENGE_ROOT = (
    "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora"
)
_REGISTRY_PATH = f"{_CHALLENGE_ROOT}/challenge_registry.json"


class ChallengeKind(StrEnum):
    """Stable challenge families for flagship benchmark stress."""

    BLINDED_HOLDOUT = "blinded_holdout"
    PERTURBATION = "perturbation"


class HoldoutOutcomeState(StrEnum):
    """Revealed outcome after frozen surfaces are checked against holdout truth."""

    HIT = "hit"
    MISS = "miss"
    OVERCONFIDENT = "overconfident"
    UNDERCONFIDENT = "underconfident"


class HoldoutOutcomeFinding(JsonModel):
    """One blinded holdout finding after hidden truth is revealed."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    frozen_surface_paths: tuple[str, ...] = Field(default_factory=tuple)
    hidden_truth_summary: str = Field(..., min_length=1)
    revealed_outcome: HoldoutOutcomeState
    note: str = Field(..., min_length=1)


class BlindedHoldoutReport(JsonModel):
    """One blinded holdout report for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    primary_package_id: str = Field(..., min_length=1)
    holdout_package_id: str = Field(..., min_length=1)
    frozen_surface_paths: tuple[str, ...] = Field(default_factory=tuple)
    withheld_truth_count: int = Field(..., ge=0)
    findings: tuple[HoldoutOutcomeFinding, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipChallengeEntry(JsonModel):
    """One durable challenge entry tracked in the product-owned registry."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    challenge_kind: ChallengeKind
    challenge_root: str = Field(..., min_length=1)
    manifest_path: str = Field(..., min_length=1)
    report_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipChallengeRegistry(JsonModel):
    """Cross-family registry for flagship holdout and perturbation challenge roots."""

    model_config = ConfigDict(extra="forbid")

    registry_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipChallengeEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def flagship_challenge_root(challenge_dir_name: str) -> str:
    """Return the durable product-owned asset root for one flagship challenge."""

    return f"{_CHALLENGE_ROOT}/{challenge_dir_name}"


def flagship_challenge_registry_path() -> str:
    """Return the checked flagship challenge registry path."""

    return _REGISTRY_PATH


def _manifest_path(challenge_root: str) -> str:
    return f"{challenge_root}/challenge_manifest.json"


def _report_path(challenge_root: str, challenge_kind: ChallengeKind) -> str:
    file_name = (
        "blinded_holdout_report.json"
        if challenge_kind is ChallengeKind.BLINDED_HOLDOUT
        else "perturbation_report.json"
    )
    return f"{challenge_root}/{file_name}"


def _review_artifact_paths(package_manifest_path: str) -> tuple[str, ...]:
    manifest = json.loads((_repo_root() / package_manifest_path).read_text(encoding="utf-8"))
    return tuple(manifest.get("expected_review_artifacts", ()))


def _generalization_reports_by_family() -> dict[str, WorkflowGeneralizationReport]:
    return {
        report.workflow_family: report for report in build_workflow_generalization_reports()
    }


def _blinded_holdout_root(workflow_family: str) -> str:
    return flagship_challenge_root(f"{workflow_family}_blinded_holdout")


def _holdout_findings(report: WorkflowGeneralizationReport) -> tuple[HoldoutOutcomeFinding, ...]:
    findings: list[HoldoutOutcomeFinding] = []
    for finding in report.findings:
        if finding.state == "survives":
            outcome = HoldoutOutcomeState.HIT
            note = (
                "the frozen benchmark and review surfaces stayed within the withheld claim boundary"
            )
        elif finding.state == "weakens":
            outcome = HoldoutOutcomeState.OVERCONFIDENT
            note = (
                "the hidden reveal showed that the frozen family claim was broader than the holdout package justifies"
            )
        else:
            outcome = HoldoutOutcomeState.MISS
            note = (
                "the hidden reveal showed that the frozen family claim does not survive the holdout package"
            )
        findings.append(
            HoldoutOutcomeFinding(
                claim_id=finding.claim_id,
                frozen_surface_paths=(
                    report.package_manifest_paths[0],
                    report.package_manifest_paths[1],
                    report.artifact_path,
                ),
                hidden_truth_summary=finding.summary,
                revealed_outcome=outcome,
                note=note,
            )
        )
    return tuple(findings)


def _build_blinded_holdout_report(workflow_family: str) -> BlindedHoldoutReport:
    report = _generalization_reports_by_family()[workflow_family]
    challenge_root = _blinded_holdout_root(workflow_family)
    frozen_surface_paths = (
        report.package_manifest_paths
        + _review_artifact_paths(report.package_manifest_paths[0])
        + _review_artifact_paths(report.package_manifest_paths[1])
        + (report.artifact_path,)
    )
    return BlindedHoldoutReport(
        challenge_id=f"{workflow_family}-blinded-holdout",
        workflow_family=workflow_family,
        artifact_path=_report_path(challenge_root, ChallengeKind.BLINDED_HOLDOUT),
        primary_package_id=report.primary_package_id,
        holdout_package_id=report.secondary_package_id,
        frozen_surface_paths=frozen_surface_paths,
        withheld_truth_count=len(report.findings),
        findings=_holdout_findings(report),
        note=(
            "This blinded holdout report freezes the main reviewer-facing package surfaces first "
            "and only then reveals whether the hidden family-transfer findings still support the "
            "same workflow posture."
        ),
    )


def build_blinded_holdout_reports() -> tuple[BlindedHoldoutReport, ...]:
    """Return the current blinded holdout reports for flagship workflow families."""

    return tuple(
        _build_blinded_holdout_report(workflow_family)
        for workflow_family in ("dda", "dia", "lfq", "ptm")
    )


def build_flagship_challenge_registry() -> FlagshipChallengeRegistry:
    """Return the registry for flagship challenge-corpus assets."""

    entries = tuple(
        FlagshipChallengeEntry(
            challenge_id=report.challenge_id,
            workflow_family=report.workflow_family,
            challenge_kind=ChallengeKind.BLINDED_HOLDOUT,
            challenge_root=_blinded_holdout_root(report.workflow_family),
            manifest_path=_manifest_path(_blinded_holdout_root(report.workflow_family)),
            report_path=report.artifact_path,
            note=(
                "This challenge root keeps frozen surfaces and revealed holdout outcomes together "
                "under a durable product-owned path."
            ),
        )
        for report in build_blinded_holdout_reports()
    )
    return FlagshipChallengeRegistry(
        registry_id="flagship-challenge-registry",
        artifact_path=_REGISTRY_PATH,
        entries=entries,
        note=(
            "The flagship challenge registry keeps blinded holdouts and adversarial perturbation "
            "corpora visible as product evidence instead of test-only sidecars."
        ),
    )


__all__ = [
    "BlindedHoldoutReport",
    "ChallengeKind",
    "FlagshipChallengeEntry",
    "FlagshipChallengeRegistry",
    "HoldoutOutcomeFinding",
    "HoldoutOutcomeState",
    "build_blinded_holdout_reports",
    "build_flagship_challenge_registry",
    "flagship_challenge_registry_path",
    "flagship_challenge_root",
]
