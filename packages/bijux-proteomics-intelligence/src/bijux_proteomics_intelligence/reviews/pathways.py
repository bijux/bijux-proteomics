# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Pathway-level review provenance and caution contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

class EnrichmentCorrectionMethod(StrEnum):
    """Multiple-testing correction method for enrichment analyses."""

    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BONFERRONI = "bonferroni"
    NONE = "none"


class EnrichmentBackgroundProvenance(JsonModel):
    """Background and statistical provenance for one enrichment output."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(..., min_length=1)
    universe_id: str = Field(..., min_length=1)
    filter_expression: str = Field(..., min_length=1)
    statistical_test: str = Field(..., min_length=1)
    correction_method: EnrichmentCorrectionMethod
    input_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_enrichment_background_provenance(
    *,
    analysis_id: str,
    universe_id: str,
    filter_expression: str,
    statistical_test: str,
    correction_method: EnrichmentCorrectionMethod,
    input_evidence_ids: tuple[str, ...],
    notes: tuple[str, ...] = (),
) -> EnrichmentBackgroundProvenance:
    """Record universe, filter, test, correction, and evidence provenance."""

    if not input_evidence_ids:
        raise ValueError("enrichment provenance requires input evidence pointers")

    return EnrichmentBackgroundProvenance(
        analysis_id=analysis_id,
        universe_id=universe_id,
        filter_expression=filter_expression,
        statistical_test=statistical_test,
        correction_method=correction_method,
        input_evidence_ids=tuple(sorted(set(input_evidence_ids))),
        notes=tuple(sorted(set(notes))),
    )


class PathwayInterpretationState(StrEnum):
    """Interpretation class for pathway/network outputs."""

    EXPLORATORY = "exploratory"
    SUPPORTED = "supported"
    MECHANISTIC_CLAIM_REFUSED = "mechanistic_claim_refused"


class PathwayCautionIssue(JsonModel):
    """Caution issue attached to one pathway interpretation output."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PathwayCautionReport(JsonModel):
    """Caution model separating exploratory interpretation from mechanism claims."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    interpretation_state: PathwayInterpretationState
    supporting_evidence_count: int = Field(..., ge=0)
    contradiction_count: int = Field(..., ge=0)
    issue_list: tuple[PathwayCautionIssue, ...] = Field(default_factory=tuple)


def build_pathway_network_caution_report(
    *,
    pathway_id: str,
    supporting_evidence_count: int,
    contradiction_count: int,
    claims_mechanistic_truth: bool,
) -> PathwayCautionReport:
    """Classify pathway/network interpretation while refusing unsupported mechanism claims."""

    issues: list[PathwayCautionIssue] = []
    if supporting_evidence_count < 2:
        issues.append(
            PathwayCautionIssue(
                code="limited_support",
                message="pathway interpretation is based on sparse evidence",
            )
        )
    if contradiction_count > 0:
        issues.append(
            PathwayCautionIssue(
                code="contradicted",
                message="pathway evidence contains unresolved contradictions",
            )
        )
    if claims_mechanistic_truth and (
        supporting_evidence_count < 4 or contradiction_count > 0
    ):
        issues.append(
            PathwayCautionIssue(
                code="mechanistic_overreach",
                message="mechanistic claim refused without convergent contradiction-free evidence",
            )
        )
        state = PathwayInterpretationState.MECHANISTIC_CLAIM_REFUSED
    elif supporting_evidence_count >= 4 and contradiction_count == 0:
        state = PathwayInterpretationState.SUPPORTED
    else:
        state = PathwayInterpretationState.EXPLORATORY

    return PathwayCautionReport(
        pathway_id=pathway_id,
        interpretation_state=state,
        supporting_evidence_count=supporting_evidence_count,
        contradiction_count=contradiction_count,
        issue_list=tuple(issues),
    )
