# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Review-ready bundle, PTM confidence, and provenance contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    ModifiedPeptide as CanonicalModifiedPeptide,
    PSMRecord as CanonicalPsmRecord,
    PeptideRecord as CanonicalPeptideRecord,
    ProteinGroup as CanonicalProteinGroup,
    ProteinRecord as CanonicalProteinRecord,
    RejectedEvidence as CanonicalRejectedEvidence,
    TargetDecoyState,
)
from bijux_proteomics.scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_tsv_rows
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.evidence import (
    PeptideSummaryReport,
    ProteinSummaryReport,
    PsmSummaryReport,
    build_peptide_summary_report,
    build_protein_summary_report,
    build_psm_summary_report,
)
from bijux_proteomics.identification.contracts.fdr_levels import (
    AcceptedPsmProvenanceReport,
    build_accepted_psm_provenance_report,
)
from bijux_proteomics.identification.contracts.confidence import (
    GroupedConfidenceReport,
    build_grouped_confidence_report,
)
from bijux_proteomics.identification.contracts.protein_review import (
    CombinedEvidenceReport,
    PeptideProteinTraceReport,
    build_combined_evidence_report,
    build_peptide_protein_trace_report,
)
from bijux_proteomics.identification.contracts.psm import (
    PsmParseReport,
    PsmRecord,
    SearchResultColumnMapping,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.contracts.score_fdr import (
    FdrPolicy,
)

class SearchResultProvenanceManifest(JsonModel):
    """Stable manifest for one search-result parsing and filtering operation."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_path: str | None = None
    source_sha256: str | None = None
    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    column_mapping: SearchResultColumnMapping
    decoy_policy: TargetDecoyLabelPolicy
    fdr_policy: FdrPolicy | None = None



class ReviewReadyEvidenceBundle(JsonModel):
    """Production-ready evidence bundle for downstream scientific review."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    threshold: float = Field(..., ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    psm_summary: PsmSummaryReport
    peptide_summary: PeptideSummaryReport
    protein_summary: ProteinSummaryReport
    accepted_psm_provenance: AcceptedPsmProvenanceReport
    grouped_confidence: GroupedConfidenceReport
    combined_evidence: CombinedEvidenceReport
    peptide_traces: PeptideProteinTraceReport


class PtmIdentificationObservation(JsonModel):
    """Minimal PTM localization evidence needed for identification confidence checks."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    localization_score: float = Field(..., ge=0.0, le=1.0)
    candidate_site_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel


class PtmIdentificationConfidenceIssue(JsonModel):
    """One validation issue for PTM-specific identification confidence."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")


class PtmIdentificationConfidenceEntry(JsonModel):
    """PTM evidence row plus site-confidence validation outcome."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    valid: bool
    issues: tuple[PtmIdentificationConfidenceIssue, ...] = Field(default_factory=tuple)


class PtmIdentificationConfidenceReport(JsonModel):
    """Validation summary for PTM-specific identification confidence claims."""

    model_config = ConfigDict(extra="forbid")

    q_value_threshold: float = Field(..., ge=0.0, le=1.0)
    min_localization_score: float = Field(..., ge=0.0, le=1.0)
    entries: tuple[PtmIdentificationConfidenceEntry, ...] = Field(default_factory=tuple)



def validate_ptm_identification_confidence(
    observations: tuple[PtmIdentificationObservation, ...],
    *,
    q_value_threshold: float = 0.05,
    min_localization_score: float = 0.75,
) -> PtmIdentificationConfidenceReport:
    """Validate whether PTM-specific identifications are strong enough for review."""
    entries: list[PtmIdentificationConfidenceEntry] = []
    for observation in observations:
        issues: list[PtmIdentificationConfidenceIssue] = []
        if observation.target_decoy_label is TargetDecoyLabel.DECOY:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="decoy_ptm_evidence",
                    message="decoy PTM evidence cannot support a biological site claim",
                    severity="error",
                )
            )
        if observation.q_value > q_value_threshold:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="q_value_above_threshold",
                    message=(
                        f"q-value {observation.q_value:.4f} exceeds the PTM identification threshold"
                    ),
                    severity="error",
                )
            )
        if observation.localization_score < min_localization_score:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="weak_localization_score",
                    message=(
                        "PTM localization score is below the minimum site-confidence threshold"
                    ),
                    severity="warning",
                )
            )
        if observation.candidate_site_count > 1:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="ambiguous_site_localization",
                    message="multiple candidate PTM sites remain plausible for this identification",
                    severity="warning",
                )
            )
        entries.append(
            PtmIdentificationConfidenceEntry(
                spectrum_id=observation.spectrum_id,
                canonical_peptide=observation.canonical_peptide,
                valid=not any(issue.severity == "error" for issue in issues),
                issues=tuple(issues),
            )
        )
    return PtmIdentificationConfidenceReport(
        q_value_threshold=q_value_threshold,
        min_localization_score=min_localization_score,
        entries=tuple(entries),
    )



def build_review_ready_evidence_bundle(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float = 0.05,
    score_orientation: str = "higher_better",
    ptm_site_keys_by_peptide: dict[str, tuple[str, ...]] | None = None,
    quant_support_by_protein: dict[str, dict[str, float | None]] | None = None,
) -> ReviewReadyEvidenceBundle:
    """Build a review-ready evidence bundle without requiring raw search output."""
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="review_ready_evidence_bundle",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    bundle = ReviewReadyEvidenceBundle(
        document_schema=schema,
        threshold=threshold,
        score_orientation=score_orientation,
        psm_summary=build_psm_summary_report(records),
        peptide_summary=build_peptide_summary_report(records),
        protein_summary=build_protein_summary_report(records),
        accepted_psm_provenance=build_accepted_psm_provenance_report(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
        grouped_confidence=build_grouped_confidence_report(records),
        combined_evidence=build_combined_evidence_report(
            records,
            ptm_site_keys_by_peptide=ptm_site_keys_by_peptide,
            quant_support_by_protein=quant_support_by_protein,
        ),
        peptide_traces=build_peptide_protein_trace_report(records),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def export_review_ready_evidence_bundle(
    bundle: ReviewReadyEvidenceBundle,
    path: Path,
) -> None:
    """Write a stable JSON evidence bundle for downstream review."""
    path.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


def build_search_result_provenance_manifest(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    decoy_policy: TargetDecoyLabelPolicy,
    fdr_policy: FdrPolicy | None = None,
) -> SearchResultProvenanceManifest:
    """Build a stable provenance manifest for one parsed search-result table."""
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=source_sha256,
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(payload)}
    )

__all__ = [
    'SearchResultProvenanceManifest',
    'ReviewReadyEvidenceBundle',
    'PtmIdentificationObservation',
    'PtmIdentificationConfidenceIssue',
    'PtmIdentificationConfidenceEntry',
    'PtmIdentificationConfidenceReport',
    'validate_ptm_identification_confidence',
    'build_review_ready_evidence_bundle',
    'export_review_ready_evidence_bundle',
    'build_search_result_provenance_manifest',
]
