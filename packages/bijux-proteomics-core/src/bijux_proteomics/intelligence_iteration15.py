# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Intelligence and review production surfaces for iteration 15."""

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
    if claims_mechanistic_truth and (supporting_evidence_count < 4 or contradiction_count > 0):
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


class QuantOutlierObservation(JsonModel):
    """Observed quant outlier bound to run/sample/protein context."""

    model_config = ConfigDict(extra="forbid")

    outlier_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    z_score: float
    batch_id: str = Field(..., min_length=1)


class RunQcSummaryLink(JsonModel):
    """QC linkage for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    qc_disposition: str = Field(..., min_length=1)
    qc_issue_codes: tuple[str, ...] = Field(default_factory=tuple)


class OutlierQcIntegratedEntry(JsonModel):
    """One outlier with integrated QC and batch/sample metadata context."""

    model_config = ConfigDict(extra="forbid")

    outlier_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    z_score: float
    qc_disposition: str = Field(..., min_length=1)
    qc_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    triage_priority: int = Field(..., ge=1, le=3)


class OutlierQcIntegratedReport(JsonModel):
    """Outlier analysis integrated with quant, QC, batch, and sample metadata."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[OutlierQcIntegratedEntry, ...] = Field(default_factory=tuple)


def build_outlier_qc_integrated_report(
    *,
    outliers: tuple[QuantOutlierObservation, ...],
    qc_summaries: tuple[RunQcSummaryLink, ...],
) -> OutlierQcIntegratedReport:
    """Connect outliers to run QC summaries, batch assignment, and sample-level metadata."""

    qc_by_run = {summary.run_id: summary for summary in qc_summaries}
    entries: list[OutlierQcIntegratedEntry] = []

    for outlier in outliers:
        qc = qc_by_run.get(outlier.run_id)
        if qc is None:
            qc_disposition = "unknown"
            qc_issue_codes: tuple[str, ...] = ()
            triage_priority = 3
        else:
            qc_disposition = qc.qc_disposition
            qc_issue_codes = qc.qc_issue_codes
            if qc.qc_disposition in {"failed", "refused"}:
                triage_priority = 1
            elif abs(outlier.z_score) >= 3.0 or qc_issue_codes:
                triage_priority = 2
            else:
                triage_priority = 3

        entries.append(
            OutlierQcIntegratedEntry(
                outlier_id=outlier.outlier_id,
                sample_id=outlier.sample_id,
                run_id=outlier.run_id,
                protein_id=outlier.protein_id,
                batch_id=outlier.batch_id,
                z_score=outlier.z_score,
                qc_disposition=qc_disposition,
                qc_issue_codes=qc_issue_codes,
                triage_priority=triage_priority,
            )
        )

    entries.sort(key=lambda entry: (entry.triage_priority, entry.outlier_id))
    return OutlierQcIntegratedReport(entries=tuple(entries))


class EvidenceGraphCandidate(JsonModel):
    """Candidate projection from the evidence graph for prioritization."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    lab_feasibility: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    missing_evidence_penalty: float = Field(..., ge=0.0, le=1.0)


class CandidatePriorityEntry(JsonModel):
    """Prioritization entry for one evidence-graph candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    priority_score: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)


class CandidatePriorityReport(JsonModel):
    """Candidate ranking by evidence strength, novelty, feasibility, and risk."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CandidatePriorityEntry, ...] = Field(default_factory=tuple)


def prioritize_candidates_from_evidence_graph(
    candidates: tuple[EvidenceGraphCandidate, ...],
) -> CandidatePriorityReport:
    """Rank candidates from evidence graph features without hiding risk penalties."""

    if not candidates:
        return CandidatePriorityReport(entries=())

    scored = [
        (
            candidate.candidate_id,
            0.35 * candidate.evidence_strength
            + 0.2 * candidate.novelty_score
            + 0.25 * candidate.lab_feasibility
            + 0.1 * (1.0 - candidate.risk_score)
            + 0.1 * (1.0 - candidate.missing_evidence_penalty),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))

    entries = tuple(
        CandidatePriorityEntry(candidate_id=candidate_id, priority_score=score, rank=index + 1)
        for index, (candidate_id, score) in enumerate(scored)
    )
    return CandidatePriorityReport(entries=entries)


class MultiObjectiveRankingInput(JsonModel):
    """Candidate objective inputs for multi-objective ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    lab_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    cost_penalty: float = Field(..., ge=0.0, le=1.0)
    risk_penalty: float = Field(..., ge=0.0, le=1.0)
    expected_gain_score: float = Field(..., ge=0.0, le=1.0)


class MultiObjectiveRankingEntry(JsonModel):
    """Multi-objective score and ranking result for one candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    objective_score: float
    rank: int = Field(..., ge=1)


class MultiObjectiveRankingReport(JsonModel):
    """Ranking report across evidence, novelty, feasibility, cost, risk, and gain."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MultiObjectiveRankingEntry, ...] = Field(default_factory=tuple)


def build_multi_objective_ranking_report(
    candidates: tuple[MultiObjectiveRankingInput, ...],
) -> MultiObjectiveRankingReport:
    """Rank candidates across weighted objectives while keeping penalties explicit."""

    scored = [
        (
            candidate.candidate_id,
            0.24 * candidate.evidence_score
            + 0.14 * candidate.novelty_score
            + 0.2 * candidate.lab_feasibility_score
            + 0.22 * candidate.expected_gain_score
            + 0.1 * (1.0 - candidate.cost_penalty)
            + 0.1 * (1.0 - candidate.risk_penalty),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return MultiObjectiveRankingReport(
        entries=tuple(
            MultiObjectiveRankingEntry(
                candidate_id=candidate_id,
                objective_score=score,
                rank=index + 1,
            )
            for index, (candidate_id, score) in enumerate(scored)
        )
    )
