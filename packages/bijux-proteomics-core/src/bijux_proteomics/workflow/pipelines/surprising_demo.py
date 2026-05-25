# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shipped surprising demo runner over compact review-grade example inputs."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
from enum import StrEnum
from io import StringIO
from pathlib import Path
import re
from time import perf_counter

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import PtmProteinCorrectionMode
from bijux_proteomics.quantification import (
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.review.biological_claim_validation import (
    BiologicalClaimDirection,
    BiologicalClaimStatus,
    BiologicalClaimValidationEntry,
)
from bijux_proteomics.targeted import (
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
    TargetedResultSourceKind,
)
from bijux_proteomics.workflow.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    build_biological_result_report_bundle_from_quant_table,
    export_biological_result_report_bundle,
)
from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyResult,
    build_proteomics_study_result_from_biological_report_bundle,
)
from bijux_proteomics.workflow.pipelines.advanced_ptm import (
    AdvancedPtmWorkflowConfig,
    AdvancedPtmWorkflowReport,
    run_advanced_ptm_workflow,
)
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    AdvancedTargetedAssayReliabilityStatus,
    TargetedValidationWorkflowConfig,
    TargetedValidationWorkflowReport,
    run_targeted_validation_workflow,
)
from bijux_proteomics.workflow.pipelines.advanced_tmt import (
    AdvancedTmtProteinConfidenceStatus,
    AdvancedTmtWorkflowConfig,
    AdvancedTmtWorkflowReport,
    run_advanced_tmt_workflow,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.belief_audit import (
    BeliefAuditReport,
    render_belief_audit_tsv,
    build_belief_audit,
)
from bijux_proteomics_intelligence.contradictions import (
    ClaimContradictionReport,
    render_claim_contradictions_tsv,
    find_claim_contradictions,
)
from bijux_proteomics_knowledge.memory.integrity.graph import build_evidence_graph
from bijux_proteomics_knowledge.memory.models.claims import (
    ClaimEvidenceState,
    ClaimPolarity,
    ClaimResolutionState,
    ClaimStatus,
    ClaimType,
    EvidenceClaim,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceExtractionMethod,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)


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
    biological_feature_tsv: str = Field(..., min_length=1)
    biological_design_tsv: str = Field(..., min_length=1)
    biological_pathway_tsv: str = Field(..., min_length=1)
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
    supported_claim_count: int = Field(..., ge=0)
    rejected_claim_count: int = Field(..., ge=0)
    belief_audit_count: int = Field(..., ge=0)
    contradiction_count: int = Field(..., ge=0)


class SurprisingDemoArtifactPaths(JsonModel):
    """Stable artifact locations written by the surprising demo runner."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    findings_tsv: str = Field(..., min_length=1)
    report_json: str = Field(..., min_length=1)
    tmt_output_dir: str = Field(..., min_length=1)
    ptm_output_dir: str = Field(..., min_length=1)
    biological_output_dir: str = Field(..., min_length=1)
    targeted_output_dir: str = Field(..., min_length=1)
    biological_report_manifest_json: str = Field(..., min_length=1)
    biological_report_html: str = Field(..., min_length=1)
    evidence_graph_nodes_tsv: str = Field(..., min_length=1)
    evidence_graph_edges_tsv: str = Field(..., min_length=1)
    protein_cards_tsv: str = Field(..., min_length=1)
    ptm_cards_tsv: str = Field(..., min_length=1)
    pathway_activity_tsv: str = Field(..., min_length=1)
    mechanism_cards_tsv: str = Field(..., min_length=1)
    qc_packets_tsv: str = Field(..., min_length=1)
    matrices_tsv: str = Field(..., min_length=1)
    assay_panel_tsv: str = Field(..., min_length=1)
    claims_tsv: str = Field(..., min_length=1)
    contradictions_tsv: str = Field(..., min_length=1)
    belief_audit_tsv: str = Field(..., min_length=1)


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
    study_result: ProteomicsStudyResult
    biological_report_manifest: BiologicalResultReportExportManifest
    claim_report: tuple[EvidenceClaim, ...] = Field(default_factory=tuple)
    contradiction_report: ClaimContradictionReport
    belief_audit_report: BeliefAuditReport
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
    """Run the shipped surprising demo and write one integrated governed bundle."""

    example_root = surprising_demo_root() if config.example_root is None else config.example_root
    manifest = load_surprising_demo_manifest(example_root)
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    start = perf_counter()
    tmt_output_dir = output_dir / "tmt_review"
    ptm_output_dir = output_dir / "ptm_review"
    biological_output_dir = output_dir / "biological_review"
    targeted_output_dir = output_dir / "targeted_validation"
    targeted_discovery_claims = _load_targeted_discovery_claims(
        _resolve_example_path(example_root, manifest.targeted_discovery_claims_json)
    )
    targeted_panel_assays = _load_targeted_panel_assays(
        _resolve_example_path(example_root, manifest.targeted_panel_assays_json)
    )

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
            discovery_claims=targeted_discovery_claims,
            panel_assays=targeted_panel_assays,
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            case_condition="treatment",
            control_condition="control",
        )
    )
    biological_report = _build_demo_biological_report(
        example_root=example_root,
        manifest=manifest,
        ptm_report=ptm_report,
    )
    study_result = build_proteomics_study_result_from_biological_report_bundle(
        biological_report
    )
    biological_manifest = export_biological_result_report_bundle(
        biological_report,
        biological_output_dir,
    )
    biological_manifest_name = "biological_report_manifest.json"
    (biological_output_dir / biological_manifest_name).write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    claim_report = _build_demo_claims(biological_report)
    evidence_bundle = _build_demo_evidence_bundle(claim_report)
    contradiction_report = find_claim_contradictions(claim_report)
    belief_audit_report = build_belief_audit(
        claim_report,
        build_evidence_graph(evidence_bundle, claims=list(claim_report)),
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
        supported_claim_count=(
            0
            if biological_report.claim_validation_report is None
            else biological_report.claim_validation_report.summary.supported_claim_count
        ),
        rejected_claim_count=(
            0
            if biological_report.claim_validation_report is None
            else biological_report.claim_validation_report.summary.rejected_claim_count
        ),
        belief_audit_count=belief_audit_report.summary.claim_count,
        contradiction_count=contradiction_report.summary.pair_count,
    )
    artifacts = _write_surprising_demo_artifacts(
        output_dir=output_dir,
        findings=findings,
        summary=summary,
        biological_manifest=biological_manifest,
        ptm_report=ptm_report,
        targeted_panel_assays=targeted_panel_assays,
        claim_report=claim_report,
        contradiction_report=contradiction_report,
        belief_audit_report=belief_audit_report,
    )
    report = SurprisingDemoReport(
        example_root=str(example_root),
        manifest_path=str(example_root / "manifest.json"),
        summary=summary,
        findings=findings,
        artifacts=artifacts,
        tmt_report=tmt_report,
        ptm_report=ptm_report,
        study_result=study_result,
        biological_report_manifest=biological_manifest,
        claim_report=claim_report,
        contradiction_report=contradiction_report,
        belief_audit_report=belief_audit_report,
        targeted_report=targeted_report,
        note=(
            "The surprising demo is a compact shipped dataset that preserves one strong "
            "protein, one downgraded protein, one PTM ambiguity, one targeted QC issue, "
            "and one validation candidate through owned workflow outputs, then routes the "
            "same local evidence into biological cards, claims, contradictions, belief "
            "audit, and report surfaces without requiring external files."
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
                "supported_claim_count": report.summary.supported_claim_count,
                "rejected_claim_count": report.summary.rejected_claim_count,
                "belief_audit_count": report.summary.belief_audit_count,
                "contradiction_count": report.summary.contradiction_count,
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


def _build_demo_biological_report(
    *,
    example_root: Path,
    manifest: SurprisingDemoManifest,
    ptm_report: AdvancedPtmWorkflowReport,
) -> BiologicalResultReportBundle:
    feature_path = _resolve_example_path(example_root, manifest.biological_feature_tsv)
    parse_report = parse_ms1_feature_table(feature_path)
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=3,
    )
    design_entries = tuple(
        parse_experimental_design_table(
            _resolve_example_path(example_root, manifest.biological_design_tsv)
        ).accepted_entries
    )
    return build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=_resolve_example_path(example_root, manifest.ptm_proteins_fasta),
        pathway_membership_tsv_path=_resolve_example_path(
            example_root,
            manifest.biological_pathway_tsv,
        ),
        condition_a="control",
        condition_b="treated",
        selection_policy=BiologicalResultSelectionPolicy(
            max_adjusted_p_value=0.2,
            min_absolute_log2_fold_change=0.3,
        ),
        ptm_evidence_card_report=ptm_report.ptm_workflow.report.evidence_cards,
    )


def _build_demo_claims(
    biological_report: BiologicalResultReportBundle,
) -> tuple[EvidenceClaim, ...]:
    claim_validation_report = biological_report.claim_validation_report
    if claim_validation_report is None:
        raise ValueError("surprising demo biological report did not produce claim validation")

    entries = (
        claim_validation_report.supported_claims
        + claim_validation_report.rejected_claims
    )
    return tuple(_build_demo_claim(entry) for entry in entries)


def _build_demo_claim(entry: BiologicalClaimValidationEntry) -> EvidenceClaim:
    direction = _demo_claim_direction(entry.asserted_direction)
    evidence_ids = tuple(
        _stable_demo_id(source_id) for source_id in entry.source_ids
    ) or (_stable_demo_id(f"{entry.claim_id}:source"),)
    return EvidenceClaim(
        claim_id=_stable_demo_id(entry.claim_id),
        target_id=_stable_demo_id(f"{entry.claim_kind.value}:{entry.subject_id}"),
        statement=entry.claim_text,
        subject=entry.subject_id,
        relation=entry.claim_kind.value,
        object=direction,
        condition=f"{entry.condition_a}_vs_{entry.condition_b}",
        direction=direction,
        magnitude=entry.effect_size,
        claim_type=(
            ClaimType.BIOMARKER
            if entry.claim_kind.value == "protein_abundance_change"
            else ClaimType.MECHANISTIC
        ),
        evidence_ids=list(evidence_ids),
        assumptions=(
            [reason.value for reason in entry.reason_codes]
            if entry.status is BiologicalClaimStatus.REJECTED
            else []
        ),
        resolution_assays=["demo_follow_up_assay"],
        status=(
            ClaimStatus.SUPPORTED
            if entry.status is BiologicalClaimStatus.SUPPORTED
            else ClaimStatus.INSUFFICIENT
        ),
        polarity=ClaimPolarity.SUPPORTING,
        resolution_state=(
            ClaimResolutionState.CLOSED
            if entry.status is BiologicalClaimStatus.SUPPORTED
            else ClaimResolutionState.OPEN
        ),
        evidence_state=(
            ClaimEvidenceState.SUPPORTED
            if entry.status is BiologicalClaimStatus.SUPPORTED
            else ClaimEvidenceState.UNRESOLVED
        ),
        confidence=0.88 if entry.status is BiologicalClaimStatus.SUPPORTED else 0.52,
        decision_impact="demo_review",
    )


def _build_demo_evidence_bundle(
    claims: tuple[EvidenceClaim, ...],
) -> EvidenceBundle:
    records: list[EvidenceRecord] = []
    seen_record_ids: set[str] = set()
    for claim in claims:
        for evidence_id in claim.evidence_ids:
            if evidence_id in seen_record_ids:
                continue
            seen_record_ids.add(evidence_id)
            records.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    kind=EvidenceKind.DIFFERENTIAL_PROTEOMICS,
                    title=evidence_id,
                    source="surprising_demo",
                    source_type=EvidenceSourceType.CURATED_NOTE,
                    origin=EvidenceOrigin.OBSERVED,
                    extraction_method=EvidenceExtractionMethod.AUTOMATED_IMPORT,
                    assay_modality="proteomics_demo",
                    biological_system="surprising_demo",
                    species="Homo sapiens",
                    quantitative_support=QuantitativeSupport(effect_size=claim.magnitude),
                    claim=claim.statement,
                    related_targets=[claim.target_id],
                    decision_tags=["demo_review"],
                    confidence=claim.confidence,
                    strength=(
                        EvidenceStrength.DECISIVE
                        if claim.confidence >= 0.8
                        else EvidenceStrength.SUPPORTING
                    ),
                    observed_at=datetime.now(UTC),
                )
            )
    return EvidenceBundle(
        bundle_id="surprising_demo_bundle",
        target_id="surprising_demo_target",
        records=records,
    )


def _demo_claim_direction(direction: BiologicalClaimDirection) -> str:
    return {
        BiologicalClaimDirection.UP: "up",
        BiologicalClaimDirection.DOWN: "down",
        BiologicalClaimDirection.MIXED: "mixed",
        BiologicalClaimDirection.UNRESOLVED: "unchanged",
    }[direction]


def _stable_demo_id(value: str) -> str:
    normalized = value.lower().replace("/", ":")
    normalized = re.sub(r"[^a-z0-9._:-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


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
        source_surface="workflow.pipelines.advanced_tmt.run_advanced_tmt_workflow",
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
        source_surface="workflow.pipelines.advanced_tmt.run_advanced_tmt_workflow",
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
        source_surface="workflow.pipelines.advanced_ptm.run_advanced_ptm_workflow",
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
        source_surface="workflow.pipelines.advanced_targeted.run_targeted_validation_workflow",
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
        source_surface="workflow.pipelines.advanced_targeted.run_targeted_validation_workflow",
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
    biological_manifest: BiologicalResultReportExportManifest,
    ptm_report: AdvancedPtmWorkflowReport,
    targeted_panel_assays: tuple[TargetedValidationPanelAssayInput, ...],
    claim_report: tuple[EvidenceClaim, ...],
    contradiction_report: ClaimContradictionReport,
    belief_audit_report: BeliefAuditReport,
) -> SurprisingDemoArtifactPaths:
    summary_name = "surprising_demo_summary.tsv"
    findings_name = "surprising_demo_findings.tsv"
    report_name = "surprising_demo_report.json"
    qc_packets_name = "demo_qc_packets.tsv"
    matrices_name = "demo_matrices.tsv"
    assay_panel_name = "demo_assay_panel.tsv"
    claims_name = "demo_claims.tsv"
    contradictions_name = "demo_claim_contradictions.tsv"
    belief_audit_name = "demo_belief_audit.tsv"
    artifacts = SurprisingDemoArtifactPaths(
        summary_tsv=summary_name,
        findings_tsv=findings_name,
        report_json=report_name,
        tmt_output_dir="tmt_review",
        ptm_output_dir="ptm_review",
        biological_output_dir="biological_review",
        targeted_output_dir="targeted_validation",
        biological_report_manifest_json="biological_review/biological_report_manifest.json",
        biological_report_html=(
            "biological_review/" + biological_manifest.artifacts.report_html
        ),
        evidence_graph_nodes_tsv=(
            "biological_review/" + biological_manifest.artifacts.evidence_graph_nodes_tsv
        ),
        evidence_graph_edges_tsv=(
            "biological_review/" + biological_manifest.artifacts.evidence_graph_edges_tsv
        ),
        protein_cards_tsv=(
            "biological_review/" + biological_manifest.artifacts.protein_card_tsv
        ),
        ptm_cards_tsv="ptm_review/" + ptm_report.manifest.artifacts.evidence_card_tsv,
        pathway_activity_tsv=(
            "biological_review/"
            + biological_manifest.artifacts.pathway_activity_condition_comparison_tsv
        ),
        mechanism_cards_tsv=(
            "biological_review/"
            + biological_manifest.artifacts.protein_mechanism_card_tsv
        ),
        qc_packets_tsv=qc_packets_name,
        matrices_tsv=matrices_name,
        assay_panel_tsv=assay_panel_name,
        claims_tsv=claims_name,
        contradictions_tsv=contradictions_name,
        belief_audit_tsv=belief_audit_name,
    )
    (output_dir / summary_name).write_text(
        _render_surprising_demo_summary_tsv(summary),
        encoding="utf-8",
    )
    (output_dir / findings_name).write_text(
        _render_surprising_demo_findings_tsv(findings),
        encoding="utf-8",
    )
    (output_dir / qc_packets_name).write_text(
        _render_demo_qc_packets_tsv(output_dir),
        encoding="utf-8",
    )
    (output_dir / matrices_name).write_text(
        _render_demo_matrix_index_tsv(biological_manifest, ptm_report),
        encoding="utf-8",
    )
    (output_dir / assay_panel_name).write_text(
        _render_demo_assay_panel_tsv(targeted_panel_assays),
        encoding="utf-8",
    )
    (output_dir / claims_name).write_text(
        _render_demo_claims_tsv(claim_report),
        encoding="utf-8",
    )
    (output_dir / contradictions_name).write_text(
        render_claim_contradictions_tsv(contradiction_report.entries),
        encoding="utf-8",
    )
    (output_dir / belief_audit_name).write_text(
        render_belief_audit_tsv(belief_audit_report.entries),
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
                "supported_claim_count": summary.supported_claim_count,
                "rejected_claim_count": summary.rejected_claim_count,
                "belief_audit_count": summary.belief_audit_count,
                "contradiction_count": summary.contradiction_count,
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


def _render_demo_qc_packets_tsv(output_dir: Path) -> str:
    rows: list[dict[str, object]] = []
    for row in _read_tsv_rows(output_dir / "tmt_review" / "tmt_validation_weak.tsv"):
        rows.append(
            {
                "qc_surface": "tmt_channel_validation",
                "subject_id": row["sample_id"],
                "condition": "",
                "status": row["issue_kind"],
                "reason": row["note"],
                "artifact_path": "tmt_review/tmt_validation_weak.tsv",
            }
        )
    for row in _read_tsv_rows(
        output_dir / "targeted_validation" / "targeted_assay_qc_unreliable_targets.tsv"
    ):
        rows.append(
            {
                "qc_surface": "targeted_assay_qc",
                "subject_id": row["sample_id"] or row["target_id"],
                "condition": row["condition"],
                "status": row["quality_flags"] or "unreliable_target",
                "reason": row["reasons"],
                "artifact_path": "targeted_validation/targeted_assay_qc_unreliable_targets.tsv",
            }
        )
    return _dict_rows_to_tsv(rows)


def _render_demo_matrix_index_tsv(
    biological_manifest: BiologicalResultReportExportManifest,
    ptm_report: AdvancedPtmWorkflowReport,
) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "matrix_kind": "protein_heatmap",
                "artifact_path": "biological_review/" + biological_manifest.artifacts.heatmap_matrix_tsv,
                "note": "z-scored protein matrix from the integrated biological review",
            },
            {
                "matrix_kind": "pathway_activity",
                "artifact_path": "biological_review/"
                + biological_manifest.artifacts.pathway_activity_matrix_tsv,
                "note": "pathway activity matrix over the compact demo cohort",
            },
            {
                "matrix_kind": "ptm_exact_sites",
                "artifact_path": "ptm_review/" + ptm_report.manifest.artifacts.exact_site_matrix_tsv,
                "note": "exact-site PTM quantification matrix after ambiguity exclusion",
            },
            {
                "matrix_kind": "targeted_samples",
                "artifact_path": "targeted_validation/targeted_matrix_samples.tsv",
                "note": "sample-level targeted validation matrix with retained and excluded transitions",
            },
        ]
    )


def _render_demo_assay_panel_tsv(
    panel_assays: tuple[TargetedValidationPanelAssayInput, ...],
) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "assay_entry_id": assay.assay_entry_id,
                "candidate_id": assay.biomarker_candidate_id,
                "candidate_kind": assay.biomarker_candidate_kind.value,
                "display_label": assay.biomarker_display_label,
                "target_protein_ref": assay.target_protein_ref,
                "peptide_sequence": assay.peptide_sequence,
                "precursor_charge": assay.precursor_charge,
                "selected_transition_count": assay.selected_transition_count,
                "exported_transition_count": assay.exported_transition_count,
                "warning_note": assay.warning_note or "",
            }
            for assay in panel_assays
        ]
    )


def _render_demo_claims_tsv(claims: tuple[EvidenceClaim, ...]) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "claim_id": claim.claim_id,
                "target_id": claim.target_id,
                "statement": claim.statement,
                "condition": claim.condition or "",
                "direction": claim.direction or "",
                "confidence": claim.confidence,
                "evidence_ids": ";".join(claim.evidence_ids),
                "assumptions": ";".join(claim.assumptions),
                "resolution_assays": ";".join(claim.resolution_assays),
                "status": claim.status.value,
            }
            for claim in claims
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
