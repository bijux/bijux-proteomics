# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic next-step recommendations over exported proteomics artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.review.claims.result_queries import (
    _GraphNodeArtifact,
    _PtmCardArtifact,
    _QcRunArtifact,
    _ResultArtifactContext,
    _load_result_artifact_context,
    _read_tsv_rows,
)
from bijux_proteomics_foundation import JsonModel


class AnalysisRecommendationKind(StrEnum):
    """Stable recommendation families over governed result artifacts."""

    RUN_PTM_CORRECTION = "run_ptm_correction"
    INSPECT_CONTAMINATION = "inspect_contamination"
    EXCLUDE_FAILED_RUN = "exclude_failed_run"
    AVOID_BATCH_CORRECTION = "avoid_batch_correction"


class AnalysisRecommendationPriority(StrEnum):
    """Relative action urgency for one deterministic recommendation."""

    HIGH = "high"
    MODERATE = "moderate"


class AnalysisRecommendation(JsonModel):
    """One deterministic next-step recommendation tied to a detected condition."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(..., min_length=1)
    recommendation_kind: AnalysisRecommendationKind
    priority: AnalysisRecommendationPriority
    data_types: tuple[str, ...] = Field(default_factory=tuple)
    detected_condition_code: str = Field(..., min_length=1)
    detected_condition_summary: str = Field(..., min_length=1)
    recommendation: str = Field(..., min_length=1)
    result_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    result_row_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class AnalysisRecommendationSummary(JsonModel):
    """Summary over one deterministic recommendation pass."""

    model_config = ConfigDict(extra="forbid")

    recommendation_count: int = Field(..., ge=0)
    detected_data_types: tuple[str, ...] = Field(default_factory=tuple)
    triggered_condition_codes: tuple[str, ...] = Field(default_factory=tuple)


class AnalysisRecommendationReport(JsonModel):
    """Deterministic next-step recommendations over result artifacts."""

    model_config = ConfigDict(extra="forbid")

    recommendations: tuple[AnalysisRecommendation, ...] = Field(default_factory=tuple)
    summary: AnalysisRecommendationSummary
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _BatchEffectSummaryArtifact:
    batch_field: str
    disposition: str
    flagged_batch_count: int
    fully_confounded_with_condition: bool
    batch_correction_blocked: bool
    batch_warning: str | None
    note: str


def build_analysis_recommendation_report_from_artifacts(
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
    batch_effect_summary_tsv_path: Path | None = None,
) -> AnalysisRecommendationReport:
    """Recommend next analysis actions from governed artifact conditions."""

    context = _load_result_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    batch_summary = (
        None
        if batch_effect_summary_tsv_path is None
        else _load_batch_effect_summary(batch_effect_summary_tsv_path)
    )
    detected_data_types = _detected_data_types(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        context=context,
        batch_summary=batch_summary,
    )
    recommendations = tuple(
        sorted(
            (
                *_ptm_correction_recommendations(context.ptm_cards, context.graph_nodes),
                *_failed_run_recommendations(context.qc_runs, context.graph_nodes),
                *_contamination_recommendations(context.qc_runs, context.graph_nodes),
                *_batch_recommendations(batch_summary),
            ),
            key=lambda entry: (
                entry.priority != AnalysisRecommendationPriority.HIGH,
                entry.recommendation_kind.value,
                entry.recommendation_id,
            ),
        )
    )
    return AnalysisRecommendationReport(
        recommendations=recommendations,
        summary=AnalysisRecommendationSummary(
            recommendation_count=len(recommendations),
            detected_data_types=detected_data_types,
            triggered_condition_codes=tuple(
                dict.fromkeys(
                    entry.detected_condition_code for entry in recommendations
                )
            ),
        ),
        note=(
            "analysis recommendations stay deterministic and are emitted only from "
            "explicit detected artifact conditions rather than static operator checklists"
        ),
    )


def render_analysis_recommendation_summary_tsv(
    report: AnalysisRecommendationReport,
) -> str:
    """Render one-row recommendation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "recommendation_count",
            "detected_data_types",
            "triggered_condition_codes",
        )
    )
    writer.writerow(
        (
            report.summary.recommendation_count,
            ";".join(report.summary.detected_data_types),
            ";".join(report.summary.triggered_condition_codes),
        )
    )
    return buffer.getvalue()


def render_analysis_recommendation_tsv(report: AnalysisRecommendationReport) -> str:
    """Render deterministic next-step recommendations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "recommendation_id",
            "recommendation_kind",
            "priority",
            "data_types",
            "detected_condition_code",
            "detected_condition_summary",
            "recommendation",
            "result_surfaces",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for entry in report.recommendations:
        writer.writerow(
            (
                entry.recommendation_id,
                entry.recommendation_kind.value,
                entry.priority.value,
                ";".join(entry.data_types),
                entry.detected_condition_code,
                entry.detected_condition_summary,
                entry.recommendation,
                ";".join(entry.result_surfaces),
                ";".join(entry.result_row_ids),
                ";".join(entry.graph_node_ids),
                entry.note,
            )
        )
    return buffer.getvalue()


def _load_batch_effect_summary(path: Path) -> _BatchEffectSummaryArtifact:
    rows = _read_tsv_rows(path)
    if len(rows) != 1:
        raise ValueError("batch effect summary TSV must contain exactly one data row")
    row = rows[0]
    return _BatchEffectSummaryArtifact(
        batch_field=row["batch_field"],
        disposition=row["disposition"],
        flagged_batch_count=int(row["flagged_batch_count"]),
        fully_confounded_with_condition=_parse_tsv_bool(
            row["fully_confounded_with_condition"]
        ),
        batch_correction_blocked=_parse_tsv_bool(row["batch_correction_blocked"]),
        batch_warning=row["batch_warning"] or None,
        note=row["note"],
    )


def _detected_data_types(
    *,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    context: _ResultArtifactContext,
    batch_summary: _BatchEffectSummaryArtifact | None,
) -> tuple[str, ...]:
    detected: list[str] = []
    if biological_report_dir is not None:
        detected.append("protein_biological")
    if ptm_report_dir is not None:
        detected.append("ptm_site")
    if context.qc_runs:
        detected.append("run_qc")
    if batch_summary is not None:
        detected.append("batch_effect")
    return tuple(detected)


def _ptm_correction_recommendations(
    cards: tuple[_PtmCardArtifact, ...],
    graph_nodes: tuple[_GraphNodeArtifact, ...],
) -> tuple[AnalysisRecommendation, ...]:
    rows = [
        card
        for card in cards
        if card.protein_correction_status == "not_requested"
    ]
    if not rows:
        return ()
    row_ids = tuple(card.card_id for card in rows)
    graph_node_ids = tuple(
        dict.fromkeys(
            node.node_id
            for card in rows
            for node in graph_nodes
            if node.entity_type == "protein" and node.entity_ref == card.protein_ref
        )
    )
    return (
        AnalysisRecommendation(
            recommendation_id="ptm-protein-correction",
            recommendation_kind=AnalysisRecommendationKind.RUN_PTM_CORRECTION,
            priority=AnalysisRecommendationPriority.MODERATE,
            data_types=("ptm_site",),
            detected_condition_code="ptm_protein_correction_not_requested",
            detected_condition_summary=(
                f"{len(rows)} PTM evidence cards preserved differential signal "
                "without protein correction"
            ),
            recommendation=(
                "run PTM protein correction before interpreting site-level changes as "
                "site-specific regulation"
            ),
            result_surfaces=("ptm_evidence_cards",),
            result_row_ids=row_ids,
            graph_node_ids=graph_node_ids,
            note="recommendation is triggered directly by PTM evidence-card correction status",
        ),
    )


def _failed_run_recommendations(
    qc_runs: tuple[_QcRunArtifact, ...],
    graph_nodes: tuple[_GraphNodeArtifact, ...],
) -> tuple[AnalysisRecommendation, ...]:
    recommendations: list[AnalysisRecommendation] = []
    for run in sorted(qc_runs, key=lambda entry: entry.run_id):
        if run.qc_status != "fail":
            continue
        graph_node_ids = _run_graph_node_ids(run.run_id, graph_nodes)
        recommendations.append(
            AnalysisRecommendation(
                recommendation_id=f"exclude-run:{run.run_id}",
                recommendation_kind=AnalysisRecommendationKind.EXCLUDE_FAILED_RUN,
                priority=AnalysisRecommendationPriority.HIGH,
                data_types=("run_qc",),
                detected_condition_code="failed_run_qc",
                detected_condition_summary=(
                    f"run {run.run_id} failed QC with reason codes "
                    f"{', '.join(run.status_reason_codes) or 'none'}"
                ),
                recommendation=(
                    f"exclude failed run {run.run_id} from biological interpretation "
                    "until the QC failure is resolved"
                ),
                result_surfaces=("run_qc_assessment",),
                result_row_ids=(run.run_id,),
                graph_node_ids=graph_node_ids,
                note="recommendation is triggered by exported run-level QC fail status",
            )
        )
    return tuple(recommendations)


def _contamination_recommendations(
    qc_runs: tuple[_QcRunArtifact, ...],
    graph_nodes: tuple[_GraphNodeArtifact, ...],
) -> tuple[AnalysisRecommendation, ...]:
    recommendations: list[AnalysisRecommendation] = []
    for run in sorted(qc_runs, key=lambda entry: entry.run_id):
        contamination_reasons = tuple(
            code
            for code in run.status_reason_codes
            if "contamin" in code.lower()
        )
        contamination_messages = tuple(
            message for message in run.messages if "contamin" in message.lower()
        )
        if not contamination_reasons and not contamination_messages:
            continue
        graph_node_ids = _run_graph_node_ids(run.run_id, graph_nodes)
        recommendations.append(
            AnalysisRecommendation(
                recommendation_id=f"inspect-contamination:{run.run_id}",
                recommendation_kind=AnalysisRecommendationKind.INSPECT_CONTAMINATION,
                priority=AnalysisRecommendationPriority.HIGH
                if run.qc_status == "fail"
                else AnalysisRecommendationPriority.MODERATE,
                data_types=("run_qc",),
                detected_condition_code="elevated_contamination",
                detected_condition_summary=(
                    f"run {run.run_id} preserved contamination signals "
                    f"{', '.join(contamination_reasons) or '; '.join(contamination_messages)}"
                ),
                recommendation=(
                    f"inspect contamination burden in run {run.run_id} before "
                    "accepting downstream biological interpretation"
                ),
                result_surfaces=("run_qc_assessment",),
                result_row_ids=(run.run_id,),
                graph_node_ids=graph_node_ids,
                note="recommendation is triggered by contaminant-specific QC reasons or messages",
            )
        )
    return tuple(recommendations)


def _batch_recommendations(
    summary: _BatchEffectSummaryArtifact | None,
) -> tuple[AnalysisRecommendation, ...]:
    if summary is None:
        return ()
    if not (summary.batch_correction_blocked or summary.fully_confounded_with_condition):
        return ()
    return (
        AnalysisRecommendation(
            recommendation_id="avoid-batch-correction",
            recommendation_kind=AnalysisRecommendationKind.AVOID_BATCH_CORRECTION,
            priority=AnalysisRecommendationPriority.HIGH,
            data_types=("batch_effect",),
            detected_condition_code="batch_condition_confounding",
            detected_condition_summary=(
                "batch summary reports full confounding between batch and condition "
                "and blocks correction"
            ),
            recommendation=(
                "avoid batch correction because batch is confounded with condition "
                "and correction would distort the biological contrast"
            ),
            result_surfaces=("batch_effect_summary",),
            result_row_ids=("batch_effect_summary",),
            graph_node_ids=(),
            note=summary.note,
        ),
    )


def _run_graph_node_ids(
    run_id: str,
    graph_nodes: tuple[_GraphNodeArtifact, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            node.node_id
            for node in graph_nodes
            if node.entity_type == "run" and node.entity_ref == run_id
        )
    )


def _parse_tsv_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    raise ValueError(f"unsupported TSV boolean value: {value}")


__all__ = [
    "AnalysisRecommendation",
    "AnalysisRecommendationKind",
    "AnalysisRecommendationPriority",
    "AnalysisRecommendationReport",
    "AnalysisRecommendationSummary",
    "build_analysis_recommendation_report_from_artifacts",
    "render_analysis_recommendation_summary_tsv",
    "render_analysis_recommendation_tsv",
]
