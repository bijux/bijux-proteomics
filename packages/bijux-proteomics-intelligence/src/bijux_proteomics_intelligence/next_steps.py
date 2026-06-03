# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic next-experiment recommendations over governed study results."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyConclusionKind,
    ProteomicsStudyResult,
)
from bijux_proteomics_foundation import JsonModel

_FAILED_QC_STATUSES = {"fail", "failed", "blocked"}
_LOW_LOCALIZATION_TIERS = {"ambiguous", "low", "low_confidence", "unlocalized"}


class NextExperimentRecommendationType(StrEnum):
    """Stable follow-up experiment families over governed result surfaces."""

    SAMPLE_QC_RERUN = "sample_qc_rerun"
    PTM_RELOCALIZATION = "ptm_relocalization"
    TARGETED_VALIDATION = "targeted_validation"
    PATHWAY_MEMBER_RESOLUTION = "pathway_member_resolution"
    REJECTED_CLAIM_RESOLUTION = "rejected_claim_resolution"


class NextExperimentRecommendationEntry(JsonModel):
    """One concrete next-experiment recommendation with explicit triggers."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    recommendation_type: NextExperimentRecommendationType
    triggering_evidence: tuple[str, ...] = Field(default_factory=tuple)
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)


class NextExperimentRecommendationSummary(JsonModel):
    """Stable summary over one recommendation pass."""

    model_config = ConfigDict(extra="forbid")

    recommendation_count: int = Field(..., ge=0)
    sample_qc_rerun_count: int = Field(..., ge=0)
    ptm_relocalization_count: int = Field(..., ge=0)
    targeted_validation_count: int = Field(..., ge=0)
    pathway_member_resolution_count: int = Field(..., ge=0)
    rejected_claim_resolution_count: int = Field(..., ge=0)


class NextExperimentRecommendationReport(JsonModel):
    """Owned recommendation surface for concrete next experiments."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[NextExperimentRecommendationEntry, ...] = Field(
        default_factory=tuple
    )
    summary: NextExperimentRecommendationSummary
    note: str = Field(..., min_length=1)


def recommend_next_experiments(
    result: ProteomicsStudyResult,
) -> NextExperimentRecommendationReport:
    """Recommend concrete next experiments from explicit result weaknesses and opportunities."""

    entries = tuple(_sorted_entries(_collect_entries(result)))
    return NextExperimentRecommendationReport(
        entries=entries,
        summary=NextExperimentRecommendationSummary(
            recommendation_count=len(entries),
            sample_qc_rerun_count=sum(
                entry.recommendation_type
                is NextExperimentRecommendationType.SAMPLE_QC_RERUN
                for entry in entries
            ),
            ptm_relocalization_count=sum(
                entry.recommendation_type
                is NextExperimentRecommendationType.PTM_RELOCALIZATION
                for entry in entries
            ),
            targeted_validation_count=sum(
                entry.recommendation_type
                is NextExperimentRecommendationType.TARGETED_VALIDATION
                for entry in entries
            ),
            pathway_member_resolution_count=sum(
                entry.recommendation_type
                is NextExperimentRecommendationType.PATHWAY_MEMBER_RESOLUTION
                for entry in entries
            ),
            rejected_claim_resolution_count=sum(
                entry.recommendation_type
                is NextExperimentRecommendationType.REJECTED_CLAIM_RESOLUTION
                for entry in entries
            ),
        ),
        note=(
            "next-experiment recommendations are emitted only when a governed study "
            "result carries an explicit weakness or opportunity that justifies a "
            "concrete follow-up experiment"
        ),
    )


def render_next_experiments_tsv(
    entries: tuple[NextExperimentRecommendationEntry, ...],
) -> str:
    """Render next-experiment recommendation rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "recommendation_id",
            "entity_id",
            "recommendation_type",
            "triggering_evidence",
            "required_inputs",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.recommendation_id,
                entry.entity_id,
                entry.recommendation_type.value,
                ";".join(entry.triggering_evidence),
                ";".join(entry.required_inputs),
            )
        )
    return handle.getvalue()


def _collect_entries(
    result: ProteomicsStudyResult,
) -> list[NextExperimentRecommendationEntry]:
    entries: list[NextExperimentRecommendationEntry] = []
    bundle = result.interactive_result_bundle
    if bundle is not None:
        for qc_entry in bundle.qc_entries:
            if _is_failed_qc(qc_entry.status, qc_entry.severity):
                entries.append(
                    NextExperimentRecommendationEntry(
                        recommendation_id=(
                            f"sample_qc_rerun:{qc_entry.entity_id}:{qc_entry.qc_id}"
                        ),
                        entity_id=qc_entry.entity_id,
                        recommendation_type=(
                            NextExperimentRecommendationType.SAMPLE_QC_RERUN
                        ),
                        triggering_evidence=(qc_entry.qc_id, *qc_entry.reason_codes),
                        required_inputs=(
                            "sample_material",
                            "instrument_method",
                            "qc_failure_review",
                        ),
                    )
                )

        for site in bundle.ptm_sites:
            if _needs_ptm_relocalization(site):
                entries.append(
                    NextExperimentRecommendationEntry(
                        recommendation_id=f"ptm_relocalization:{site.site_key}",
                        entity_id=site.site_key,
                        recommendation_type=(
                            NextExperimentRecommendationType.PTM_RELOCALIZATION
                        ),
                        triggering_evidence=tuple(
                            dict.fromkeys(
                                (
                                    site.site_key,
                                    *site.warning_codes,
                                    *site.claim_ids,
                                    *site.sample_ids,
                                )
                            )
                        ),
                        required_inputs=(
                            "site_localizing_fragmentation",
                            "protein_baseline_matrix",
                            "modified_peptide_review",
                        ),
                    )
                )

        for protein in bundle.proteins:
            if _supports_targeted_validation(protein):
                entries.append(
                    NextExperimentRecommendationEntry(
                        recommendation_id=(
                            f"targeted_validation:{protein.representative_protein_ref}"
                        ),
                        entity_id=protein.representative_protein_ref,
                        recommendation_type=(
                            NextExperimentRecommendationType.TARGETED_VALIDATION
                        ),
                        triggering_evidence=tuple(
                            dict.fromkeys(
                                (
                                    protein.object_id,
                                    *protein.peptide_ids,
                                    *protein.graph_node_ids,
                                )
                            )
                        ),
                        required_inputs=(
                            "target_peptide_panel",
                            "transition_design",
                            "orthogonal_quant_readout",
                        ),
                    )
                )

        for pathway in bundle.pathways:
            if pathway.unresolved_member_ids:
                entries.append(
                    NextExperimentRecommendationEntry(
                        recommendation_id=f"pathway_member_resolution:{pathway.pathway_id}",
                        entity_id=pathway.pathway_id,
                        recommendation_type=(
                            NextExperimentRecommendationType.PATHWAY_MEMBER_RESOLUTION
                        ),
                        triggering_evidence=tuple(
                            dict.fromkeys(
                                (
                                    pathway.pathway_id,
                                    *pathway.supporting_protein_refs,
                                    *pathway.unresolved_member_ids,
                                )
                            )
                        ),
                        required_inputs=(
                            "member_target_list",
                            "orthogonal_member_assay",
                            "pathway_context_review",
                        ),
                    )
                )

    for conclusion in result.biological_conclusions:
        if conclusion.kind is ProteomicsStudyConclusionKind.REJECTED_CLAIM:
            entries.append(
                NextExperimentRecommendationEntry(
                    recommendation_id=(
                        f"rejected_claim_resolution:{conclusion.conclusion_id}"
                    ),
                    entity_id=conclusion.subject_id,
                    recommendation_type=(
                        NextExperimentRecommendationType.REJECTED_CLAIM_RESOLUTION
                    ),
                    triggering_evidence=(
                        conclusion.conclusion_id,
                        conclusion.subject_id,
                        conclusion.evidence_surface,
                    ),
                    required_inputs=(
                        "missing_support_review",
                        "orthogonal_resolution_assay",
                    ),
                )
            )

    return entries


def _sorted_entries(
    entries: list[NextExperimentRecommendationEntry],
) -> tuple[NextExperimentRecommendationEntry, ...]:
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.recommendation_type.value,
                entry.entity_id,
                entry.recommendation_id,
            ),
        )
    )


def _is_failed_qc(status: str, severity: str | None) -> bool:
    normalized_status = status.strip().lower()
    normalized_severity = "" if severity is None else severity.strip().lower()
    return (
        normalized_status in _FAILED_QC_STATUSES
        or normalized_severity in _FAILED_QC_STATUSES
    )


def _needs_ptm_relocalization(site: object) -> bool:
    localization_tier = getattr(site, "localization_tier", None)
    normalized_tier = "" if localization_tier is None else localization_tier.lower()
    warning_codes = set(getattr(site, "warning_codes", ()))
    return (
        normalized_tier in _LOW_LOCALIZATION_TIERS
        or "low_localization" in warning_codes
        or "ambiguous_localization" in warning_codes
        or "missing_protein_baseline" in warning_codes
    )


def _supports_targeted_validation(protein: object) -> bool:
    significant = getattr(protein, "significant", None)
    peptide_ids = tuple(getattr(protein, "peptide_ids", ()))
    warning_codes = tuple(getattr(protein, "warning_codes", ()))
    return significant is True and len(peptide_ids) >= 2 and not warning_codes


__all__ = [
    "NextExperimentRecommendationEntry",
    "NextExperimentRecommendationReport",
    "NextExperimentRecommendationSummary",
    "NextExperimentRecommendationType",
    "recommend_next_experiments",
    "render_next_experiments_tsv",
]
