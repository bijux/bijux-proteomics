# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compact evidence-constrained summaries for collaborator-facing result handoff."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.review.claims.analysis_recommendations import (
    AnalysisRecommendationReport,
    build_analysis_recommendation_report_from_artifacts,
)
from bijux_proteomics.review.claims.result_queries import (
    _ResultArtifactContext,
    _empty_to_none,
    _find_protein_card,
    _load_result_artifact_context,
    _node_ids_for_entity,
    _parse_optional_float,
    _protein_card_graph_node_ids,
    _read_tsv_rows,
    _sample_to_failed_qc_runs,
    _split_multi,
)
from bijux_proteomics_foundation import JsonModel


class CompactResultSummarySectionKind(StrEnum):
    """Stable collaborator-summary sections over governed result artifacts."""

    SAMPLE_QC = "sample_qc"
    STRONGEST_FINDINGS = "strongest_findings"
    WEAK_FINDINGS = "weak_findings"
    FAILED_ASSUMPTIONS = "failed_assumptions"
    NEXT_VALIDATION_TARGETS = "next_validation_targets"


_SECTION_TITLES = {
    CompactResultSummarySectionKind.SAMPLE_QC: "Sample QC",
    CompactResultSummarySectionKind.STRONGEST_FINDINGS: "Strongest findings",
    CompactResultSummarySectionKind.WEAK_FINDINGS: "Weak findings",
    CompactResultSummarySectionKind.FAILED_ASSUMPTIONS: "Failed assumptions",
    CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS: "Next validation targets",
}


class CompactResultSummaryEntry(JsonModel):
    """One compact collaborator-facing summary bullet with explicit citations."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    section_kind: CompactResultSummarySectionKind
    subject_id: str | None = None
    subject_label: str | None = None
    confidence_label: str | None = None
    summary_text: str = Field(..., min_length=1)
    result_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    result_row_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CompactResultSummarySection(JsonModel):
    """One named collaborator-summary section with short evidence bullets."""

    model_config = ConfigDict(extra="forbid")

    section_kind: CompactResultSummarySectionKind
    title: str = Field(..., min_length=1)
    entries: tuple[CompactResultSummaryEntry, ...] = Field(default_factory=tuple)


class CompactResultSummaryOverview(JsonModel):
    """Compact counts over one collaborator summary."""

    model_config = ConfigDict(extra="forbid")

    section_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    sample_qc_entry_count: int = Field(..., ge=0)
    strongest_finding_count: int = Field(..., ge=0)
    weak_finding_count: int = Field(..., ge=0)
    failed_assumption_count: int = Field(..., ge=0)
    next_validation_target_count: int = Field(..., ge=0)


class CompactResultSummaryReport(JsonModel):
    """Owned compact summary report constrained by validated evidence surfaces."""

    model_config = ConfigDict(extra="forbid")

    sections: tuple[CompactResultSummarySection, ...] = Field(default_factory=tuple)
    overview: CompactResultSummaryOverview
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _ClaimArtifact:
    claim_id: str
    claim_kind: str
    subject_id: str
    subject_label: str
    claim_text: str
    adjusted_p_value: float | None
    effect_size: float | None
    robustness_score: float | None
    evidence_tier: str | None
    confidence_tier: str | None
    pathway_delta: float | None
    regulator_score: float | None
    reason_codes: tuple[str, ...]
    source_ids: tuple[str, ...]
    validation_note: str


@dataclass(frozen=True)
class _HypothesisArtifact:
    hypothesis_id: str
    subject_id: str
    subject_label: str
    claim: str
    evidence_node_ids: tuple[str, ...]
    confidence_score: float | None
    confidence_tier: str
    next_experiment_suggestion: str
    source_ids: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class _SectionConfidenceArtifact:
    section_key: str
    section_title: str
    confidence_label: str
    rationale: str


@dataclass(frozen=True)
class _SummaryArtifactContext:
    result_context: _ResultArtifactContext
    supported_claims: tuple[_ClaimArtifact, ...]
    rejected_claims: tuple[_ClaimArtifact, ...]
    hypotheses: tuple[_HypothesisArtifact, ...]
    section_confidence_entries: tuple[_SectionConfidenceArtifact, ...]
    recommendation_report: AnalysisRecommendationReport


def build_compact_result_summary_report_from_artifacts(
    *,
    biological_report_dir: Path,
    ptm_report_dir: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
    batch_effect_summary_tsv_path: Path | None = None,
) -> CompactResultSummaryReport:
    """Build a short collaborator summary constrained to governed evidence artifacts."""

    context = _load_summary_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        batch_effect_summary_tsv_path=batch_effect_summary_tsv_path,
    )
    sections = (
        _build_sample_qc_section(context),
        _build_strongest_findings_section(context),
        _build_weak_findings_section(context),
        _build_failed_assumptions_section(context),
        _build_next_validation_targets_section(context),
    )
    entries = tuple(entry for section in sections for entry in section.entries)
    return CompactResultSummaryReport(
        sections=sections,
        overview=CompactResultSummaryOverview(
            section_count=len(sections),
            entry_count=len(entries),
            sample_qc_entry_count=len(sections[0].entries),
            strongest_finding_count=len(sections[1].entries),
            weak_finding_count=len(sections[2].entries),
            failed_assumption_count=len(sections[3].entries),
            next_validation_target_count=len(sections[4].entries),
        ),
        note=(
            "compact collaborator summaries remain constrained to validated claims, "
            "explicit rejections, exploratory hypotheses, QC ledgers, and deterministic "
            "recommendations so unsupported claims cannot be promoted into short handoff text"
        ),
    )


def render_compact_result_summary_markdown(
    report: CompactResultSummaryReport,
) -> str:
    """Render a compact collaborator summary as GitHub-flavored Markdown."""

    lines = ["# Compact Result Summary", ""]
    for section in report.sections:
        lines.append(f"## {section.title}")
        if not section.entries:
            lines.append("- No governed evidence entries were retained for this section.")
        else:
            for entry in section.entries:
                lines.append(f"- {entry.summary_text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_compact_result_summary_overview_tsv(
    report: CompactResultSummaryReport,
) -> str:
    """Render compact summary counts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("section_count", report.overview.section_count),
        ("entry_count", report.overview.entry_count),
        ("sample_qc_entry_count", report.overview.sample_qc_entry_count),
        ("strongest_finding_count", report.overview.strongest_finding_count),
        ("weak_finding_count", report.overview.weak_finding_count),
        ("failed_assumption_count", report.overview.failed_assumption_count),
        ("next_validation_target_count", report.overview.next_validation_target_count),
        ("note", report.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def render_compact_result_summary_entry_tsv(
    report: CompactResultSummaryReport,
) -> str:
    """Render compact collaborator summary entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entry_id",
            "section_kind",
            "subject_id",
            "subject_label",
            "confidence_label",
            "summary_text",
            "result_surfaces",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for section in report.sections:
        for entry in section.entries:
            writer.writerow(
                (
                    entry.entry_id,
                    entry.section_kind.value,
                    "" if entry.subject_id is None else entry.subject_id,
                    "" if entry.subject_label is None else entry.subject_label,
                    "" if entry.confidence_label is None else entry.confidence_label,
                    entry.summary_text,
                    ";".join(entry.result_surfaces),
                    ";".join(entry.result_row_ids),
                    ";".join(entry.graph_node_ids),
                    entry.note,
                )
            )
    return buffer.getvalue()


def _load_summary_artifact_context(
    *,
    biological_report_dir: Path,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    batch_effect_summary_tsv_path: Path | None,
) -> _SummaryArtifactContext:
    result_context = _load_result_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    recommendation_report = build_analysis_recommendation_report_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        batch_effect_summary_tsv_path=batch_effect_summary_tsv_path,
    )
    return _SummaryArtifactContext(
        result_context=result_context,
        supported_claims=_load_claim_artifacts(
            biological_report_dir / "biological_supported_claims.tsv"
        ),
        rejected_claims=_load_claim_artifacts(
            biological_report_dir / "biological_rejected_claims.tsv"
        ),
        hypotheses=_load_hypothesis_artifacts(
            biological_report_dir / "biological_hypotheses.tsv"
        ),
        section_confidence_entries=_load_section_confidence_artifacts(
            biological_report_dir / "biological_report_section_confidence.tsv"
        ),
        recommendation_report=recommendation_report,
    )


def _load_claim_artifacts(path: Path) -> tuple[_ClaimArtifact, ...]:
    return tuple(
        _ClaimArtifact(
            claim_id=row["claim_id"],
            claim_kind=row["claim_kind"],
            subject_id=row["subject_id"],
            subject_label=row["subject_label"],
            claim_text=row["claim_text"],
            adjusted_p_value=_parse_optional_float(row["adjusted_p_value"]),
            effect_size=_parse_optional_float(row["effect_size"]),
            robustness_score=_parse_optional_float(row["robustness_score"]),
            evidence_tier=_empty_to_none(row["evidence_tier"]),
            confidence_tier=_empty_to_none(row["confidence_tier"]),
            pathway_delta=_parse_optional_float(row["pathway_delta"]),
            regulator_score=_parse_optional_float(row["regulator_score"]),
            reason_codes=_split_multi(row["reason_codes"]),
            source_ids=_split_multi(row["source_ids"]),
            validation_note=row["validation_note"],
        )
        for row in _read_tsv_rows(path)
    )


def _load_hypothesis_artifacts(path: Path) -> tuple[_HypothesisArtifact, ...]:
    return tuple(
        _HypothesisArtifact(
            hypothesis_id=row["hypothesis_id"],
            subject_id=row["subject_id"],
            subject_label=row["subject_label"],
            claim=row["claim"],
            evidence_node_ids=_split_multi(row["evidence_node_ids"]),
            confidence_score=_parse_optional_float(row["confidence_score"]),
            confidence_tier=row["confidence_tier"],
            next_experiment_suggestion=row["next_experiment_suggestion"],
            source_ids=_split_multi(row["source_ids"]),
            note=row["note"],
        )
        for row in _read_tsv_rows(path)
    )


def _load_section_confidence_artifacts(
    path: Path,
) -> tuple[_SectionConfidenceArtifact, ...]:
    return tuple(
        _SectionConfidenceArtifact(
            section_key=row["section_key"],
            section_title=row["section_title"],
            confidence_label=row["confidence_label"],
            rationale=row["rationale"],
        )
        for row in _read_tsv_rows(path)
    )


def _build_sample_qc_section(
    context: _SummaryArtifactContext,
) -> CompactResultSummarySection:
    entries: list[CompactResultSummaryEntry] = []
    failed_sample_runs = _sample_to_failed_qc_runs(context.result_context)
    if failed_sample_runs:
        for sample_id, qc_runs in tuple(sorted(failed_sample_runs.items()))[:3]:
            reason_codes = sorted(
                {
                    reason
                    for run in qc_runs
                    for reason in run.status_reason_codes
                }
            )
            graph_node_ids = tuple(
                dict.fromkeys(
                    (
                        *_node_ids_for_entity(
                            context.result_context.graph_node_index,
                            entity_type="sample",
                            entity_ref=sample_id,
                        ),
                        *(
                            node_id
                            for run in qc_runs
                            for node_id in _node_ids_for_entity(
                                context.result_context.graph_node_index,
                                entity_type="run",
                                entity_ref=run.run_id,
                            )
                        ),
                    )
                )
            )
            entries.append(
                CompactResultSummaryEntry(
                    entry_id=f"sample_qc:{sample_id}",
                    section_kind=CompactResultSummarySectionKind.SAMPLE_QC,
                    subject_id=sample_id,
                    subject_label=sample_id,
                    confidence_label="failed",
                    summary_text=(
                        f"Sample {sample_id} failed run-level QC because mapped runs "
                        f"{', '.join(run.run_id for run in qc_runs)} carried fail status "
                        f"with reason codes {', '.join(reason_codes) or 'none'}."
                    ),
                    result_surfaces=("qc_assessment",),
                    result_row_ids=tuple(run.run_id for run in qc_runs),
                    graph_node_ids=graph_node_ids,
                    note="sample QC bullet is derived only from explicit failed run ledgers",
                )
            )
    elif context.result_context.qc_runs:
        entries.append(
            CompactResultSummaryEntry(
                entry_id="sample_qc:no_failures",
                section_kind=CompactResultSummarySectionKind.SAMPLE_QC,
                subject_id=None,
                subject_label=None,
                confidence_label="pass",
                summary_text=(
                    f"No samples mapped to failed QC runs across {len(context.result_context.qc_runs)} run-QC ledgers."
                ),
                result_surfaces=("qc_assessment",),
                result_row_ids=tuple(run.run_id for run in context.result_context.qc_runs),
                graph_node_ids=(),
                note="sample QC bullet is derived from explicit run-QC ledgers",
            )
        )
    else:
        entries.append(
            CompactResultSummaryEntry(
                entry_id="sample_qc:no_run_ledgers",
                section_kind=CompactResultSummarySectionKind.SAMPLE_QC,
                subject_id=None,
                subject_label=None,
                confidence_label="unknown",
                summary_text=(
                    "No run-level QC ledgers were supplied, so sample QC remains constrained to report-level confidence artifacts only."
                ),
                result_surfaces=("biological_report_section_confidence",),
                result_row_ids=(),
                graph_node_ids=(),
                note="sample QC section cannot infer pass/fail sample status without explicit QC ledgers",
            )
        )
    return CompactResultSummarySection(
        section_kind=CompactResultSummarySectionKind.SAMPLE_QC,
        title=_SECTION_TITLES[CompactResultSummarySectionKind.SAMPLE_QC],
        entries=tuple(entries),
    )


def _build_strongest_findings_section(
    context: _SummaryArtifactContext,
) -> CompactResultSummarySection:
    ordered_claims = tuple(
        sorted(context.supported_claims, key=_supported_claim_sort_key)
    )[:3]
    entries = tuple(
        _supported_claim_entry(claim, context=context, rank=index)
        for index, claim in enumerate(ordered_claims, start=1)
    )
    fallback = (
        CompactResultSummaryEntry(
            entry_id="strongest_findings:none",
            section_kind=CompactResultSummarySectionKind.STRONGEST_FINDINGS,
            subject_id=None,
            subject_label=None,
            confidence_label="none",
            summary_text="No supported validated biological claims were retained for a strongest-findings summary.",
            result_surfaces=("biological_supported_claims",),
            result_row_ids=(),
            graph_node_ids=(),
            note="strongest findings remain empty when the validation engine retains no supported claims",
        ),
    )
    return CompactResultSummarySection(
        section_kind=CompactResultSummarySectionKind.STRONGEST_FINDINGS,
        title=_SECTION_TITLES[CompactResultSummarySectionKind.STRONGEST_FINDINGS],
        entries=entries or fallback,
    )


def _build_weak_findings_section(
    context: _SummaryArtifactContext,
) -> CompactResultSummarySection:
    entries: list[CompactResultSummaryEntry] = []
    for index, hypothesis in enumerate(
        tuple(sorted(context.hypotheses, key=_hypothesis_sort_key))[:3],
        start=1,
    ):
        entries.append(
            CompactResultSummaryEntry(
                entry_id=f"weak_findings:hypothesis:{index}:{hypothesis.hypothesis_id}",
                section_kind=CompactResultSummarySectionKind.WEAK_FINDINGS,
                subject_id=hypothesis.subject_id,
                subject_label=hypothesis.subject_label,
                confidence_label=hypothesis.confidence_tier,
                summary_text=(
                    f"Exploratory hypothesis for {hypothesis.subject_label}: {hypothesis.claim} "
                    f"Next experiment: {hypothesis.next_experiment_suggestion}."
                ),
                result_surfaces=("biological_hypotheses",),
                result_row_ids=(hypothesis.hypothesis_id, *hypothesis.source_ids),
                graph_node_ids=hypothesis.evidence_node_ids,
                note="weak findings section is constrained to graph-backed exploratory hypotheses",
            )
        )
    if not entries:
        weak_sections = [
            entry
            for entry in context.section_confidence_entries
            if entry.confidence_label in {"weak", "exploratory"}
        ][:3]
        for index, entry in enumerate(weak_sections, start=1):
            entries.append(
                CompactResultSummaryEntry(
                    entry_id=f"weak_findings:section:{index}:{entry.section_key}",
                    section_kind=CompactResultSummarySectionKind.WEAK_FINDINGS,
                    subject_id=entry.section_key,
                    subject_label=entry.section_title,
                    confidence_label=entry.confidence_label,
                    summary_text=(
                        f"{entry.section_title} is {entry.confidence_label} because {entry.rationale}."
                    ),
                    result_surfaces=("biological_report_section_confidence",),
                    result_row_ids=(entry.section_key,),
                    graph_node_ids=(),
                    note="weak findings section falls back to derived section-confidence artifacts",
                )
            )
    if not entries:
        entries.append(
            CompactResultSummaryEntry(
                entry_id="weak_findings:none",
                section_kind=CompactResultSummarySectionKind.WEAK_FINDINGS,
                subject_id=None,
                subject_label=None,
                confidence_label="none",
                summary_text="No governed exploratory findings were retained for the weak-findings section.",
                result_surfaces=("biological_hypotheses",),
                result_row_ids=(),
                graph_node_ids=(),
                note="weak findings stay empty when neither hypotheses nor exploratory sections are present",
            )
        )
    return CompactResultSummarySection(
        section_kind=CompactResultSummarySectionKind.WEAK_FINDINGS,
        title=_SECTION_TITLES[CompactResultSummarySectionKind.WEAK_FINDINGS],
        entries=tuple(entries),
    )


def _build_failed_assumptions_section(
    context: _SummaryArtifactContext,
) -> CompactResultSummarySection:
    entries: list[CompactResultSummaryEntry] = []
    for index, claim in enumerate(
        tuple(sorted(context.rejected_claims, key=_rejected_claim_sort_key))[:3],
        start=1,
    ):
        entries.append(
            CompactResultSummaryEntry(
                entry_id=f"failed_assumptions:claim:{index}:{claim.claim_id}",
                section_kind=CompactResultSummarySectionKind.FAILED_ASSUMPTIONS,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                confidence_label="rejected",
                summary_text=(
                    f"Rejected claim for {claim.subject_label}: {claim.claim_text}. "
                    f"Reason codes: {', '.join(claim.reason_codes) or 'none'}."
                ),
                result_surfaces=("biological_rejected_claims",),
                result_row_ids=(claim.claim_id, *claim.source_ids),
                graph_node_ids=_graph_node_ids_for_subject(
                    subject_id=claim.subject_id,
                    source_ids=claim.source_ids,
                    context=context.result_context,
                ),
                note="failed assumptions section is constrained to explicitly rejected validated claims",
            )
        )
    if len(entries) < 3:
        invalid_sections = [
            entry
            for entry in context.section_confidence_entries
            if entry.confidence_label == "invalid"
        ][: 3 - len(entries)]
        for index, entry in enumerate(invalid_sections, start=1):
            entries.append(
                CompactResultSummaryEntry(
                    entry_id=f"failed_assumptions:section:{index}:{entry.section_key}",
                    section_kind=CompactResultSummarySectionKind.FAILED_ASSUMPTIONS,
                    subject_id=entry.section_key,
                    subject_label=entry.section_title,
                    confidence_label=entry.confidence_label,
                    summary_text=(
                        f"{entry.section_title} is invalid for collaborator narrative because {entry.rationale}."
                    ),
                    result_surfaces=("biological_report_section_confidence",),
                    result_row_ids=(entry.section_key,),
                    graph_node_ids=(),
                    note="failed assumptions section may cite invalid section-confidence artifacts",
                )
            )
    if not entries:
        entries.append(
            CompactResultSummaryEntry(
                entry_id="failed_assumptions:none",
                section_kind=CompactResultSummarySectionKind.FAILED_ASSUMPTIONS,
                subject_id=None,
                subject_label=None,
                confidence_label="none",
                summary_text="No rejected claims or invalid report sections were retained for the failed-assumptions section.",
                result_surfaces=("biological_rejected_claims",),
                result_row_ids=(),
                graph_node_ids=(),
                note="failed assumptions remain empty when no explicit rejections are exported",
            )
        )
    return CompactResultSummarySection(
        section_kind=CompactResultSummarySectionKind.FAILED_ASSUMPTIONS,
        title=_SECTION_TITLES[CompactResultSummarySectionKind.FAILED_ASSUMPTIONS],
        entries=tuple(entries),
    )


def _build_next_validation_targets_section(
    context: _SummaryArtifactContext,
) -> CompactResultSummarySection:
    entries: list[CompactResultSummaryEntry] = []
    for index, recommendation in enumerate(
        context.recommendation_report.recommendations[:3],
        start=1,
    ):
        entries.append(
            CompactResultSummaryEntry(
                entry_id=f"next_validation_targets:recommendation:{index}:{recommendation.recommendation_id}",
                section_kind=CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS,
                subject_id=None,
                subject_label=None,
                confidence_label=recommendation.priority.value,
                summary_text=recommendation.recommendation,
                result_surfaces=recommendation.result_surfaces,
                result_row_ids=recommendation.result_row_ids,
                graph_node_ids=recommendation.graph_node_ids,
                note="next validation targets section may cite deterministic recommendation actions",
            )
        )
    if len(entries) < 3:
        remaining = 3 - len(entries)
        for index, hypothesis in enumerate(
            tuple(sorted(context.hypotheses, key=_hypothesis_sort_key))[:remaining],
            start=1,
        ):
            entries.append(
                CompactResultSummaryEntry(
                    entry_id=f"next_validation_targets:hypothesis:{index}:{hypothesis.hypothesis_id}",
                    section_kind=CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS,
                    subject_id=hypothesis.subject_id,
                    subject_label=hypothesis.subject_label,
                    confidence_label=hypothesis.confidence_tier,
                    summary_text=(
                        f"Validate {hypothesis.subject_label} with: {hypothesis.next_experiment_suggestion}"
                    ),
                    result_surfaces=("biological_hypotheses",),
                    result_row_ids=(hypothesis.hypothesis_id, *hypothesis.source_ids),
                    graph_node_ids=hypothesis.evidence_node_ids,
                    note="next validation targets section may reuse graph-backed exploratory hypotheses",
                )
            )
    if not entries:
        entries.append(
            CompactResultSummaryEntry(
                entry_id="next_validation_targets:none",
                section_kind=CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS,
                subject_id=None,
                subject_label=None,
                confidence_label="none",
                summary_text="No deterministic recommendations or graph-backed hypotheses were retained for next validation targets.",
                result_surfaces=("analysis_recommendations",),
                result_row_ids=(),
                graph_node_ids=(),
                note="next validation targets remain empty when no explicit recommendation surface is available",
            )
        )
    return CompactResultSummarySection(
        section_kind=CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS,
        title=_SECTION_TITLES[CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS],
        entries=tuple(entries),
    )


def _supported_claim_sort_key(claim: _ClaimArtifact) -> tuple[float, float, float, str]:
    effect = 0.0 if claim.effect_size is None else abs(claim.effect_size)
    robustness = 0.0 if claim.robustness_score is None else claim.robustness_score
    significance = 1.0 if claim.adjusted_p_value is None else claim.adjusted_p_value
    return (-robustness, significance, -effect, claim.claim_id)


def _rejected_claim_sort_key(claim: _ClaimArtifact) -> tuple[int, float, str]:
    return (-len(claim.reason_codes), 1.0 if claim.adjusted_p_value is None else claim.adjusted_p_value, claim.claim_id)


def _hypothesis_sort_key(hypothesis: _HypothesisArtifact) -> tuple[float, str]:
    return (-(0.0 if hypothesis.confidence_score is None else hypothesis.confidence_score), hypothesis.hypothesis_id)


def _supported_claim_entry(
    claim: _ClaimArtifact,
    *,
    context: _SummaryArtifactContext,
    rank: int,
) -> CompactResultSummaryEntry:
    confidence = claim.evidence_tier or claim.confidence_tier or "supported"
    details = []
    if claim.adjusted_p_value is not None:
        details.append(f"adjusted p-value {claim.adjusted_p_value:.4g}")
    if claim.effect_size is not None:
        details.append(f"effect size {claim.effect_size:.4g}")
    if claim.robustness_score is not None:
        details.append(f"robustness {claim.robustness_score:.2f}")
    detail_text = "" if not details else " (" + ", ".join(details) + ")."
    return CompactResultSummaryEntry(
        entry_id=f"strongest_findings:{rank}:{claim.claim_id}",
        section_kind=CompactResultSummarySectionKind.STRONGEST_FINDINGS,
        subject_id=claim.subject_id,
        subject_label=claim.subject_label,
        confidence_label=confidence,
        summary_text=f"{claim.claim_text}.{detail_text}",
        result_surfaces=("biological_supported_claims",),
        result_row_ids=(claim.claim_id, *claim.source_ids),
        graph_node_ids=_graph_node_ids_for_subject(
            subject_id=claim.subject_id,
            source_ids=claim.source_ids,
            context=context.result_context,
        ),
        note="strongest findings section is constrained to supported validated claims only",
    )


def _graph_node_ids_for_subject(
    *,
    subject_id: str,
    source_ids: tuple[str, ...],
    context: _ResultArtifactContext,
) -> tuple[str, ...]:
    protein_card = _find_protein_card(context.protein_card_index, subject_id)
    graph_node_ids: list[str] = []
    if protein_card is not None:
        graph_node_ids.extend(_protein_card_graph_node_ids(protein_card))
    for entity_ref in (subject_id, *source_ids):
        graph_node_ids.extend(
            node.node_id
            for node in context.graph_nodes
            if node.entity_ref == entity_ref
        )
    return tuple(dict.fromkeys(graph_node_ids))


__all__ = [
    "CompactResultSummaryEntry",
    "CompactResultSummaryOverview",
    "CompactResultSummaryReport",
    "CompactResultSummarySection",
    "CompactResultSummarySectionKind",
    "build_compact_result_summary_report_from_artifacts",
    "render_compact_result_summary_entry_tsv",
    "render_compact_result_summary_markdown",
    "render_compact_result_summary_overview_tsv",
]
