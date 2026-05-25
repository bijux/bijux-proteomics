# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shipped surprising demo runner over compact review-grade example inputs."""

from __future__ import annotations

import csv
import json
from enum import StrEnum
from io import StringIO
from pathlib import Path
from time import perf_counter

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import PtmProteinCorrectionMode
from bijux_proteomics.targeted import (
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
    TargetedResultSourceKind,
)
from bijux_proteomics.workflow.advanced_ptm import (
    AdvancedPtmWorkflowConfig,
    AdvancedPtmWorkflowReport,
    run_advanced_ptm_workflow,
)
from bijux_proteomics.workflow.advanced_targeted import (
    AdvancedTargetedAssayReliabilityStatus,
    TargetedValidationWorkflowConfig,
    TargetedValidationWorkflowReport,
    run_targeted_validation_workflow,
)
from bijux_proteomics.workflow.advanced_tmt import (
    AdvancedTmtProteinConfidenceStatus,
    AdvancedTmtWorkflowConfig,
    AdvancedTmtWorkflowReport,
    run_advanced_tmt_workflow,
)
from bijux_proteomics_foundation import JsonModel


class SurprisingDemoFindingKind(StrEnum):
    """Stable phenomenon classes carried by the shipped surprising demo."""

    STRONG_PROTEIN = "strong_protein"
    WEAK_OR_DOWNGRADED_PROTEIN = "weak_or_downgraded_protein"
    PTM_AMBIGUITY = "ptm_ambiguity"
    QC_ISSUE = "qc_issue"
    VALIDATION_CANDIDATE = "validation_candidate"


class SurprisingDemoManifest(JsonModel):
    """Example-root manifest for the shipped surprising demo dataset."""

    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)
    tmt_result_tsv: str = Field(..., min_length=1)
    tmt_design_tsv: str = Field(..., min_length=1)
    ptm_evidence_tsv: str = Field(..., min_length=1)
    ptm_feature_tsv: str = Field(..., min_length=1)
    ptm_proteins_fasta: str = Field(..., min_length=1)
    ptm_design_tsv: str = Field(..., min_length=1)
    ptm_annotation_tsv: str = Field(..., min_length=1)
    targeted_result_tsv: str = Field(..., min_length=1)
    targeted_design_tsv: str = Field(..., min_length=1)
    targeted_discovery_claims_json: str = Field(..., min_length=1)
    targeted_panel_assays_json: str = Field(..., min_length=1)
    expected_strong_protein_id: str = Field(..., min_length=1)
    expected_downgraded_protein_id: str = Field(..., min_length=1)
    expected_ambiguous_site_key: str = Field(..., min_length=1)
    expected_qc_issue_candidate_id: str = Field(..., min_length=1)
    expected_validation_candidate_id: str = Field(..., min_length=1)


class SurprisingDemoConfig(JsonModel):
    """Config for running the shipped surprising demo workflow."""

    model_config = ConfigDict(extra="forbid")

    output_dir: Path
    example_root: Path | None = None


class SurprisingDemoFinding(JsonModel):
    """One required phenomenon preserved by the shipped surprising demo."""

    model_config = ConfigDict(extra="forbid")

    finding_kind: SurprisingDemoFindingKind
    subject_id: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class SurprisingDemoSummary(JsonModel):
    """Compact summary over one surprising demo execution."""

    model_config = ConfigDict(extra="forbid")

    elapsed_seconds: float = Field(..., ge=0.0)
    within_local_ten_minute_budget: bool
    strong_protein_count: int = Field(..., ge=0)
    downgraded_protein_count: int = Field(..., ge=0)
    ambiguous_ptm_count: int = Field(..., ge=0)
    qc_issue_count: int = Field(..., ge=0)
    validation_candidate_count: int = Field(..., ge=0)


class SurprisingDemoArtifactPaths(JsonModel):
    """Stable artifact locations written by the surprising demo runner."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    findings_tsv: str = Field(..., min_length=1)
    report_json: str = Field(..., min_length=1)
    tmt_output_dir: str = Field(..., min_length=1)
    ptm_output_dir: str = Field(..., min_length=1)
    targeted_output_dir: str = Field(..., min_length=1)


class SurprisingDemoReport(JsonModel):
    """Execution report over the shipped surprising demo dataset."""

    model_config = ConfigDict(extra="forbid")

    example_root: str = Field(..., min_length=1)
    manifest_path: str = Field(..., min_length=1)
    summary: SurprisingDemoSummary
    findings: tuple[SurprisingDemoFinding, ...] = Field(default_factory=tuple)
    artifacts: SurprisingDemoArtifactPaths
    tmt_report: AdvancedTmtWorkflowReport
    ptm_report: AdvancedPtmWorkflowReport
    targeted_report: TargetedValidationWorkflowReport
    note: str = Field(..., min_length=1)


def surprising_demo_root() -> Path:
    """Return the shipped surprising demo example root."""

    return _repo_root() / "examples" / "surprising_demo"


def load_surprising_demo_manifest(
    example_root: Path | None = None,
) -> SurprisingDemoManifest:
    """Load the shipped surprising demo manifest from the example root."""

    root = surprising_demo_root() if example_root is None else example_root
    manifest_path = root / "manifest.json"
    return SurprisingDemoManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )


def run_surprising_demo(config: SurprisingDemoConfig) -> SurprisingDemoReport:
    """Run the shipped surprising demo and preserve five required phenomena."""

    example_root = surprising_demo_root() if config.example_root is None else config.example_root
    manifest = load_surprising_demo_manifest(example_root)
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    start = perf_counter()
    tmt_output_dir = output_dir / "tmt_review"
    ptm_output_dir = output_dir / "ptm_review"
    targeted_output_dir = output_dir / "targeted_validation"

    tmt_report = run_advanced_tmt_workflow(
        AdvancedTmtWorkflowConfig(
            result_tsv_path=_resolve_example_path(example_root, manifest.tmt_result_tsv),
            design_tsv_path=_resolve_example_path(example_root, manifest.tmt_design_tsv),
            output_dir=tmt_output_dir,
            control_channel="126",
            condition_a="control",
            condition_b="treatment",
        )
    )
    ptm_report = run_advanced_ptm_workflow(
        AdvancedPtmWorkflowConfig(
            evidence_tsv_path=_resolve_example_path(
                example_root,
                manifest.ptm_evidence_tsv,
            ),
            proteins_fasta_path=_resolve_example_path(
                example_root,
                manifest.ptm_proteins_fasta,
            ),
            feature_tsv_path=_resolve_example_path(
                example_root,
                manifest.ptm_feature_tsv,
            ),
            design_tsv_path=_resolve_example_path(example_root, manifest.ptm_design_tsv),
            annotation_tsv_path=_resolve_example_path(
                example_root,
                manifest.ptm_annotation_tsv,
            ),
            annotation_target_species="Homo sapiens",
            output_dir=ptm_output_dir,
            condition_a="control",
            condition_b="treated",
            protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
            batch_field="",
        )
    )
    targeted_report = run_targeted_validation_workflow(
        TargetedValidationWorkflowConfig(
            result_tsv_path=_resolve_example_path(
                example_root,
                manifest.targeted_result_tsv,
            ),
            design_tsv_path=_resolve_example_path(
                example_root,
                manifest.targeted_design_tsv,
            ),
            output_dir=targeted_output_dir,
            discovery_claims=_load_targeted_discovery_claims(
                _resolve_example_path(
                    example_root,
                    manifest.targeted_discovery_claims_json,
                )
            ),
            panel_assays=_load_targeted_panel_assays(
                _resolve_example_path(
                    example_root,
                    manifest.targeted_panel_assays_json,
                )
            ),
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            case_condition="treatment",
            control_condition="control",
        )
    )
    elapsed_seconds = perf_counter() - start

    findings = (
        _build_strong_protein_finding(
            manifest.expected_strong_protein_id,
            report=tmt_report,
            output_dir=output_dir,
        ),
        _build_downgraded_protein_finding(
            manifest.expected_downgraded_protein_id,
            report=tmt_report,
            output_dir=output_dir,
        ),
        _build_ptm_ambiguity_finding(
            manifest.expected_ambiguous_site_key,
            report=ptm_report,
            output_dir=output_dir,
        ),
        _build_qc_issue_finding(
            manifest.expected_qc_issue_candidate_id,
            report=targeted_report,
            output_dir=output_dir,
        ),
        _build_validation_candidate_finding(
            manifest.expected_validation_candidate_id,
            report=targeted_report,
            output_dir=output_dir,
        ),
    )
    summary = SurprisingDemoSummary(
        elapsed_seconds=elapsed_seconds,
        within_local_ten_minute_budget=elapsed_seconds < 600.0,
        strong_protein_count=sum(
            card.confidence_status is AdvancedTmtProteinConfidenceStatus.SUPPORTED
            for card in tmt_report.evidence_cards
        ),
        downgraded_protein_count=sum(
            card.confidence_status
            is AdvancedTmtProteinConfidenceStatus.DOWNGRADED_BY_INTERFERENCE
            for card in tmt_report.evidence_cards
        ),
        ambiguous_ptm_count=ptm_report.summary.excluded_ambiguous_row_count,
        qc_issue_count=sum(
            card.assay_reliability_status
            is not AdvancedTargetedAssayReliabilityStatus.RELIABLE
            for card in targeted_report.evidence_cards
        ),
        validation_candidate_count=len(targeted_report.evidence_cards),
    )
    artifacts = _write_surprising_demo_artifacts(
        output_dir=output_dir,
        findings=findings,
        summary=summary,
    )
    report = SurprisingDemoReport(
        example_root=str(example_root),
        manifest_path=str(example_root / "manifest.json"),
        summary=summary,
        findings=findings,
        artifacts=artifacts,
        tmt_report=tmt_report,
        ptm_report=ptm_report,
        targeted_report=targeted_report,
        note=(
            "The surprising demo is a compact shipped dataset that preserves one strong "
            "protein, one downgraded protein, one PTM ambiguity, one targeted QC issue, "
            "and one validation candidate through owned workflow outputs."
        ),
    )
    (output_dir / artifacts.report_json).write_text(
        report.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return report


def render_surprising_demo_summary_tsv(report: SurprisingDemoReport) -> str:
    """Render one summary TSV for the surprising demo."""

    return _dict_rows_to_tsv(
        [
            {
                "elapsed_seconds": round(report.summary.elapsed_seconds, 6),
                "within_local_ten_minute_budget": str(
                    report.summary.within_local_ten_minute_budget
                ).lower(),
                "strong_protein_count": report.summary.strong_protein_count,
                "downgraded_protein_count": report.summary.downgraded_protein_count,
                "ambiguous_ptm_count": report.summary.ambiguous_ptm_count,
                "qc_issue_count": report.summary.qc_issue_count,
                "validation_candidate_count": report.summary.validation_candidate_count,
            }
        ]
    )


def render_surprising_demo_findings_tsv(report: SurprisingDemoReport) -> str:
    """Render one findings TSV for the surprising demo."""

    return _dict_rows_to_tsv(
        [
            {
                "finding_kind": finding.finding_kind.value,
                "subject_id": finding.subject_id,
                "source_surface": finding.source_surface,
                "artifact_path": finding.artifact_path,
                "note": finding.note,
            }
            for finding in report.findings
        ]
    )


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _resolve_example_path(example_root: Path, relative_path: str) -> Path:
    return example_root / relative_path


def _load_targeted_discovery_claims(
    path: Path,
) -> tuple[TargetedValidationDiscoveryClaimInput, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        TargetedValidationDiscoveryClaimInput.model_validate(item)
        for item in payload
    )


def _load_targeted_panel_assays(
    path: Path,
) -> tuple[TargetedValidationPanelAssayInput, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        TargetedValidationPanelAssayInput.model_validate(item)
        for item in payload
    )


def _build_strong_protein_finding(
    expected_protein_id: str,
    *,
    report: AdvancedTmtWorkflowReport,
    output_dir: Path,
) -> SurprisingDemoFinding:
    card = next(
        (
            entry
            for entry in report.evidence_cards
            if entry.protein_id == expected_protein_id
            and entry.confidence_status is AdvancedTmtProteinConfidenceStatus.SUPPORTED
        ),
        None,
    )
    if card is None:
        raise ValueError(
            f"surprising demo expected a supported strong protein for {expected_protein_id}"
        )
    return SurprisingDemoFinding(
        finding_kind=SurprisingDemoFindingKind.STRONG_PROTEIN,
        subject_id=card.protein_id,
        source_surface="workflow.advanced_tmt.run_advanced_tmt_workflow",
        artifact_path=str(
            (output_dir / "tmt_review" / report.manifest.artifacts.evidence_card_tsv).relative_to(
                output_dir
            )
        ),
        note=card.note,
    )


def _build_downgraded_protein_finding(
    expected_protein_id: str,
    *,
    report: AdvancedTmtWorkflowReport,
    output_dir: Path,
) -> SurprisingDemoFinding:
    card = next(
        (
            entry
            for entry in report.evidence_cards
            if entry.protein_id == expected_protein_id
            and entry.confidence_status
            is AdvancedTmtProteinConfidenceStatus.DOWNGRADED_BY_INTERFERENCE
        ),
        None,
    )
    if card is None:
        raise ValueError(
            f"surprising demo expected a downgraded protein for {expected_protein_id}"
        )
    return SurprisingDemoFinding(
        finding_kind=SurprisingDemoFindingKind.WEAK_OR_DOWNGRADED_PROTEIN,
        subject_id=card.protein_id,
        source_surface="workflow.advanced_tmt.run_advanced_tmt_workflow",
        artifact_path=str(
            (output_dir / "tmt_review" / report.manifest.artifacts.evidence_card_tsv).relative_to(
                output_dir
            )
        ),
        note=card.note,
    )


def _build_ptm_ambiguity_finding(
    expected_site_key: str,
    *,
    report: AdvancedPtmWorkflowReport,
    output_dir: Path,
) -> SurprisingDemoFinding:
    artifact_name = report.manifest.artifacts.excluded_ambiguous_sites_tsv
    rows = _read_tsv_rows(output_dir / "ptm_review" / artifact_name)
    row = next((entry for entry in rows if entry["site_key"] == expected_site_key), None)
    if row is None:
        raise ValueError(
            f"surprising demo expected an ambiguous PTM site for {expected_site_key}"
        )
    return SurprisingDemoFinding(
        finding_kind=SurprisingDemoFindingKind.PTM_AMBIGUITY,
        subject_id=row["site_key"],
        source_surface="workflow.advanced_ptm.run_advanced_ptm_workflow",
        artifact_path=str((output_dir / "ptm_review" / artifact_name).relative_to(output_dir)),
        note=row["reason"],
    )


def _build_qc_issue_finding(
    expected_candidate_id: str,
    *,
    report: TargetedValidationWorkflowReport,
    output_dir: Path,
) -> SurprisingDemoFinding:
    card = next(
        (
            entry
            for entry in report.evidence_cards
            if entry.candidate_id == expected_candidate_id
            and entry.assay_reliability_status
            is not AdvancedTargetedAssayReliabilityStatus.RELIABLE
        ),
        None,
    )
    if card is None:
        raise ValueError(
            f"surprising demo expected a targeted QC issue for {expected_candidate_id}"
        )
    return SurprisingDemoFinding(
        finding_kind=SurprisingDemoFindingKind.QC_ISSUE,
        subject_id=card.candidate_id,
        source_surface="workflow.advanced_targeted.run_targeted_validation_workflow",
        artifact_path=str(
            (
                output_dir
                / "targeted_validation"
                / report.manifest.artifacts.assay_qc_unreliable_targets_tsv
            ).relative_to(output_dir)
        ),
        note=card.note,
    )


def _build_validation_candidate_finding(
    expected_candidate_id: str,
    *,
    report: TargetedValidationWorkflowReport,
    output_dir: Path,
) -> SurprisingDemoFinding:
    card = next(
        (entry for entry in report.evidence_cards if entry.candidate_id == expected_candidate_id),
        None,
    )
    if card is None:
        raise ValueError(
            f"surprising demo expected a validation candidate for {expected_candidate_id}"
        )
    return SurprisingDemoFinding(
        finding_kind=SurprisingDemoFindingKind.VALIDATION_CANDIDATE,
        subject_id=card.candidate_id,
        source_surface="workflow.advanced_targeted.run_targeted_validation_workflow",
        artifact_path=str(
            (
                output_dir
                / "targeted_validation"
                / report.manifest.artifacts.evidence_cards_tsv
            ).relative_to(output_dir)
        ),
        note=card.note,
    )


def _write_surprising_demo_artifacts(
    *,
    output_dir: Path,
    findings: tuple[SurprisingDemoFinding, ...],
    summary: SurprisingDemoSummary,
) -> SurprisingDemoArtifactPaths:
    summary_name = "surprising_demo_summary.tsv"
    findings_name = "surprising_demo_findings.tsv"
    report_name = "surprising_demo_report.json"
    artifacts = SurprisingDemoArtifactPaths(
        summary_tsv=summary_name,
        findings_tsv=findings_name,
        report_json=report_name,
        tmt_output_dir="tmt_review",
        ptm_output_dir="ptm_review",
        targeted_output_dir="targeted_validation",
    )
    (output_dir / summary_name).write_text(
        _render_surprising_demo_summary_tsv(summary),
        encoding="utf-8",
    )
    (output_dir / findings_name).write_text(
        _render_surprising_demo_findings_tsv(findings),
        encoding="utf-8",
    )
    return artifacts


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return tuple({key: value for key, value in row.items()} for row in reader)


def _dict_rows_to_tsv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def _render_surprising_demo_summary_tsv(summary: SurprisingDemoSummary) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "elapsed_seconds": round(summary.elapsed_seconds, 6),
                "within_local_ten_minute_budget": str(
                    summary.within_local_ten_minute_budget
                ).lower(),
                "strong_protein_count": summary.strong_protein_count,
                "downgraded_protein_count": summary.downgraded_protein_count,
                "ambiguous_ptm_count": summary.ambiguous_ptm_count,
                "qc_issue_count": summary.qc_issue_count,
                "validation_candidate_count": summary.validation_candidate_count,
            }
        ]
    )


def _render_surprising_demo_findings_tsv(
    findings: tuple[SurprisingDemoFinding, ...],
) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "finding_kind": finding.finding_kind.value,
                "subject_id": finding.subject_id,
                "source_surface": finding.source_surface,
                "artifact_path": finding.artifact_path,
                "note": finding.note,
            }
            for finding in findings
        ]
    )


__all__ = [
    "SurprisingDemoArtifactPaths",
    "SurprisingDemoConfig",
    "SurprisingDemoFinding",
    "SurprisingDemoFindingKind",
    "SurprisingDemoManifest",
    "SurprisingDemoReport",
    "SurprisingDemoSummary",
    "load_surprising_demo_manifest",
    "render_surprising_demo_findings_tsv",
    "render_surprising_demo_summary_tsv",
    "run_surprising_demo",
    "surprising_demo_root",
]
