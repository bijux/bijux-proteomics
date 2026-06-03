# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Weak-evidence workflow validation over sparse, ambiguous, downgraded, and blocked outputs."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.lab.qc_benchmarks import (
    QcPromotionBlockObservation,
    QcPromotionBlockReport,
    build_qc_promotion_block_report,
)
from bijux_proteomics.workflow.pipelines.advanced_tmt import (
    AdvancedTmtWorkflowConfig,
    AdvancedTmtWorkflowReport,
    run_advanced_tmt_workflow,
)
from bijux_proteomics.workflow.public_benchmark_descriptors import (
    PublicBenchmarkDescriptor,
    load_public_benchmark_descriptor,
    public_benchmark_root,
)
from bijux_proteomics.workflow.pipelines.public_benchmark_runner import (
    PublicBenchmarkRunReport,
    run_public_benchmark_descriptor,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyResult,
    ProteomicsStudyResultSummary,
    build_proteomics_study_result_from_biological_report_bundle,
)
from bijux_proteomics_foundation import JsonModel


class WeakEvidenceBenchmarkStatus(StrEnum):
    """Stable benchmark outcomes for the weak-evidence benchmark."""

    PASSED = "passed"
    FAILED = "failed"


class WeakEvidenceReportSectionKey(StrEnum):
    """Section keys preserved on the weak-evidence benchmark report."""

    REFUSED_CLAIMS = "refused_claims"


class WeakEvidenceCriterionId(StrEnum):
    """Required negative-pressure checks for the weak-evidence benchmark."""

    FAILED_QC = "failed_qc"
    REFUSED_CLAIM = "refused_claim"
    DOWNGRADED_PROTEIN = "downgraded_protein"
    AMBIGUOUS_PTM = "ambiguous_ptm"
    INVALID_OR_BLOCKED_CONTRAST = "invalid_or_blocked_contrast"


class WeakEvidenceBenchmarkCriterion(JsonModel):
    """One required weak-evidence phenomenon tracked by the benchmark."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: WeakEvidenceCriterionId
    executed: bool
    observed: bool
    evidence_count: int = Field(..., ge=0)
    source_surface: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class WeakEvidenceBenchmarkSummary(JsonModel):
    """Compact benchmark summary over the required weak-evidence outcomes."""

    model_config = ConfigDict(extra="forbid")

    executed_surface_count: int = Field(..., ge=0)
    observed_negative_surface_count: int = Field(..., ge=0)
    missing_required_criterion_count: int = Field(..., ge=0)
    failed_qc_block_count: int = Field(..., ge=0)
    refused_claim_count: int = Field(..., ge=0)
    downgraded_protein_count: int = Field(..., ge=0)
    ambiguous_ptm_count: int = Field(..., ge=0)
    invalid_or_blocked_contrast_count: int = Field(..., ge=0)
    all_outputs_positive_or_accepted: bool
    status: WeakEvidenceBenchmarkStatus
    note: str = Field(..., min_length=1)


class WeakEvidenceRefusedClaimEntry(JsonModel):
    """One refused-claim row preserved from the weak-evidence benchmark fixture."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    validation_note: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)


class WeakEvidenceReportSection(JsonModel):
    """One stable section emitted by the weak-evidence benchmark report."""

    model_config = ConfigDict(extra="forbid")

    section_key: WeakEvidenceReportSectionKey
    title: str = Field(..., min_length=1)
    claim_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WeakEvidenceBenchmarkDescriptor(JsonModel):
    """Descriptor for one weak-evidence benchmark execution."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    output_root: Path
    lfq_sparse_descriptor_path: Path | None = None
    ptm_descriptor_path: Path | None = None
    tmt_result_tsv_path: Path | None = None
    tmt_design_tsv_path: Path | None = None
    tmt_control_channel: str = Field(default="126", min_length=1)
    tmt_condition_a: str | None = "control"
    tmt_condition_b: str | None = "treatment"
    qc_promotion_observations: tuple[QcPromotionBlockObservation, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class WeakEvidenceBenchmarkReport(JsonModel):
    """Execution report for the weak-evidence benchmark."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    output_root: Path
    criteria: tuple[WeakEvidenceBenchmarkCriterion, ...] = Field(default_factory=tuple)
    summary: WeakEvidenceBenchmarkSummary
    refused_claims: tuple[WeakEvidenceRefusedClaimEntry, ...] = Field(
        default_factory=tuple
    )
    sections: tuple[WeakEvidenceReportSection, ...] = Field(default_factory=tuple)
    lfq_sparse_study_result: ProteomicsStudyResult | None = None
    lfq_sparse_report: PublicBenchmarkRunReport | None = None
    ptm_report: PublicBenchmarkRunReport | None = None
    tmt_report: AdvancedTmtWorkflowReport | None = None
    qc_promotion_block_report: QcPromotionBlockReport | None = None
    note: str = Field(..., min_length=1)


def build_flagship_weak_evidence_benchmark_descriptor(
    output_root: Path,
) -> WeakEvidenceBenchmarkDescriptor:
    """Build the shipped weak-evidence benchmark descriptor."""

    multiplex_descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "multiplex_tmtpro_review_package" / "dataset.yml"
    )
    return WeakEvidenceBenchmarkDescriptor(
        benchmark_id="flagship_weak_evidence_benchmark",
        output_root=output_root,
        lfq_sparse_descriptor_path=(
            public_benchmark_root()
            / "lfq_sparse_contrast_benchmark_dataset"
            / "dataset.yml"
        ),
        ptm_descriptor_path=(
            public_benchmark_root() / "ptm_localization_review_package" / "dataset.yml"
        ),
        tmt_result_tsv_path=(
            _repo_root()
            / "packages/bijux-proteomics-core/benchmarks/public/support/tmt_interference_downgrade.tsv"
        ),
        tmt_design_tsv_path=_source_path_from_descriptor(
            multiplex_descriptor,
            schema_id="design_tsv",
        ),
        qc_promotion_observations=(
            QcPromotionBlockObservation(
                run_id="run_failed_qc_blocked",
                failed_qc=True,
                attempted_decision_promotion=True,
                promotion_prevented=True,
                blocking_reason="failed_qc_blocks_biological_promotion",
            ),
            QcPromotionBlockObservation(
                run_id="run_clean_qc_promoted",
                failed_qc=False,
                attempted_decision_promotion=True,
                promotion_prevented=False,
                blocking_reason="qc_clean_decision_allowed",
            ),
        ),
        note=(
            "The flagship weak-evidence benchmark forces sparse LFQ refusal, PTM ambiguity, "
            "interference-driven TMT downgrade from a governed support reporter table, and "
            "failed-QC promotion blocking into one review surface."
        ),
    )


def run_weak_evidence_benchmark(
    descriptor: WeakEvidenceBenchmarkDescriptor,
) -> WeakEvidenceBenchmarkReport:
    """Run the weak-evidence benchmark across owned benchmark and workflow surfaces."""

    descriptor.output_root.mkdir(parents=True, exist_ok=True)

    lfq_sparse_report = (
        None
        if descriptor.lfq_sparse_descriptor_path is None
        else run_public_benchmark_descriptor(
            descriptor.lfq_sparse_descriptor_path,
            output_root=descriptor.output_root / "public_benchmark_runs",
        )
    )
    ptm_report = (
        None
        if descriptor.ptm_descriptor_path is None
        else run_public_benchmark_descriptor(
            descriptor.ptm_descriptor_path,
            output_root=descriptor.output_root / "public_benchmark_runs",
        )
    )
    tmt_report = (
        None
        if descriptor.tmt_result_tsv_path is None or descriptor.tmt_design_tsv_path is None
        else run_advanced_tmt_workflow(
            AdvancedTmtWorkflowConfig(
                result_tsv_path=descriptor.tmt_result_tsv_path,
                design_tsv_path=descriptor.tmt_design_tsv_path,
                output_dir=descriptor.output_root / "advanced_tmt_review",
                control_channel=descriptor.tmt_control_channel,
                condition_a=descriptor.tmt_condition_a,
                condition_b=descriptor.tmt_condition_b,
            )
        )
    )
    qc_report = (
        None
        if not descriptor.qc_promotion_observations
        else build_qc_promotion_block_report(descriptor.qc_promotion_observations)
    )

    refused_claims = _load_refused_claim_entries(lfq_sparse_report)
    lfq_sparse_study_result = _build_refused_claim_study_result(
        report=lfq_sparse_report,
        refused_claims=refused_claims,
    )
    refused_claim_count = len(refused_claims)
    blocked_contrast_count = _blocked_or_invalid_contrast_count(lfq_sparse_report)
    ambiguous_ptm_count = _verified_count(ptm_report, "ambiguous_site_count")
    downgraded_protein_count = (
        0 if tmt_report is None else tmt_report.summary.downgraded_protein_count
    )
    failed_qc_block_count = (
        0 if qc_report is None else qc_report.failed_qc_blocked_count
    )

    criteria = (
        _criterion(
            criterion_id=WeakEvidenceCriterionId.FAILED_QC,
            executed=qc_report is not None,
            evidence_count=failed_qc_block_count,
            source_surface="study.qc_benchmarks.build_qc_promotion_block_report",
            message=(
                "failed QC blocks downstream decision promotion"
                if failed_qc_block_count > 0
                else "no failed-QC decision promotion block was preserved"
            ),
        ),
        _criterion(
            criterion_id=WeakEvidenceCriterionId.REFUSED_CLAIM,
            executed=lfq_sparse_report is not None,
            evidence_count=refused_claim_count,
            source_surface="workflow.pipelines.public_benchmark_runner:lfq_sparse_contrast_benchmark_dataset",
            message=(
                "sparse LFQ benchmark preserved explicit rejected biological claims"
                if refused_claim_count > 0
                else "sparse LFQ benchmark did not preserve any rejected biological claim rows"
            ),
        ),
        _criterion(
            criterion_id=WeakEvidenceCriterionId.DOWNGRADED_PROTEIN,
            executed=tmt_report is not None,
            evidence_count=downgraded_protein_count,
            source_surface="workflow.pipelines.advanced_tmt.run_advanced_tmt_workflow",
            message=(
                "advanced TMT review preserved interference-driven protein downgrades"
                if downgraded_protein_count > 0
                else "advanced TMT review produced no downgraded protein rows"
            ),
        ),
        _criterion(
            criterion_id=WeakEvidenceCriterionId.AMBIGUOUS_PTM,
            executed=ptm_report is not None,
            evidence_count=ambiguous_ptm_count,
            source_surface="workflow.pipelines.public_benchmark_runner:ptm_localization_review_package",
            message=(
                "PTM benchmark preserved ambiguous localization rows"
                if ambiguous_ptm_count > 0
                else "PTM benchmark did not preserve ambiguous site rows"
            ),
        ),
        _criterion(
            criterion_id=WeakEvidenceCriterionId.INVALID_OR_BLOCKED_CONTRAST,
            executed=lfq_sparse_report is not None,
            evidence_count=blocked_contrast_count,
            source_surface="workflow.pipelines.public_benchmark_runner:lfq_sparse_contrast_benchmark_dataset",
            message=(
                "sparse LFQ benchmark preserved blocked or invalid contrast interpretation"
                if blocked_contrast_count > 0
                else "sparse LFQ benchmark did not preserve blocked or invalid contrast outputs"
            ),
        ),
    )

    executed_surface_count = sum(criterion.executed for criterion in criteria)
    observed_negative_surface_count = sum(criterion.observed for criterion in criteria)
    missing_required_criterion_count = sum(not criterion.observed for criterion in criteria)
    all_outputs_positive_or_accepted = (
        executed_surface_count > 0 and observed_negative_surface_count == 0
    )
    status = (
        WeakEvidenceBenchmarkStatus.PASSED
        if missing_required_criterion_count == 0 and not all_outputs_positive_or_accepted
        else WeakEvidenceBenchmarkStatus.FAILED
    )

    summary = WeakEvidenceBenchmarkSummary(
        executed_surface_count=executed_surface_count,
        observed_negative_surface_count=observed_negative_surface_count,
        missing_required_criterion_count=missing_required_criterion_count,
        failed_qc_block_count=failed_qc_block_count,
        refused_claim_count=refused_claim_count,
        downgraded_protein_count=downgraded_protein_count,
        ambiguous_ptm_count=ambiguous_ptm_count,
        invalid_or_blocked_contrast_count=blocked_contrast_count,
        all_outputs_positive_or_accepted=all_outputs_positive_or_accepted,
        status=status,
        note=(
            "The weak-evidence benchmark passed because every required negative-evidence "
            "surface remained explicit."
            if status is WeakEvidenceBenchmarkStatus.PASSED
            else "The weak-evidence benchmark failed because one or more required "
            "negative-evidence surfaces were missing or all evaluated outputs were "
            "positive or accepted."
        ),
    )
    sections = (
        WeakEvidenceReportSection(
            section_key=WeakEvidenceReportSectionKey.REFUSED_CLAIMS,
            title="Refused Claims",
            claim_ids=tuple(entry.claim_id for entry in refused_claims),
            note=(
                "The refused-claims section is loaded from weak-evidence rejected claim rows "
                "so sparse or unresolved biology remains explicit in the final benchmark report."
            ),
        ),
    )

    return WeakEvidenceBenchmarkReport(
        benchmark_id=descriptor.benchmark_id,
        output_root=descriptor.output_root,
        criteria=criteria,
        summary=summary,
        refused_claims=refused_claims,
        sections=sections,
        lfq_sparse_study_result=lfq_sparse_study_result,
        lfq_sparse_report=lfq_sparse_report,
        ptm_report=ptm_report,
        tmt_report=tmt_report,
        qc_promotion_block_report=qc_report,
        note=(
            "This benchmark keeps benchmark-run refusal, ambiguity, downgrade, and QC-block "
            "surfaces together so workflows cannot look strong simply because weak evidence "
            "was dropped."
        ),
    )


def render_weak_evidence_benchmark_summary_tsv(
    report: WeakEvidenceBenchmarkReport,
) -> str:
    """Render the benchmark summary as a one-row-per-metric TSV."""

    rows = (
        ("benchmark_id", report.benchmark_id),
        ("status", report.summary.status.value),
        ("executed_surface_count", report.summary.executed_surface_count),
        (
            "observed_negative_surface_count",
            report.summary.observed_negative_surface_count,
        ),
        (
            "missing_required_criterion_count",
            report.summary.missing_required_criterion_count,
        ),
        ("failed_qc_block_count", report.summary.failed_qc_block_count),
        ("refused_claim_count", report.summary.refused_claim_count),
        ("downgraded_protein_count", report.summary.downgraded_protein_count),
        ("ambiguous_ptm_count", report.summary.ambiguous_ptm_count),
        (
            "invalid_or_blocked_contrast_count",
            report.summary.invalid_or_blocked_contrast_count,
        ),
        (
            "all_outputs_positive_or_accepted",
            str(report.summary.all_outputs_positive_or_accepted).lower(),
        ),
        ("note", report.summary.note),
    )
    return "\n".join(
        "\t".join((str(key), str(value)))
        for key, value in (("metric_id", "value"), *rows)
    )


def render_weak_evidence_benchmark_criteria_tsv(
    report: WeakEvidenceBenchmarkReport,
) -> str:
    """Render one explicit row per benchmark criterion."""

    lines = [
        "criterion_id\texecuted\tobserved\tevidence_count\tsource_surface\tmessage"
    ]
    lines.extend(
        "\t".join(
            (
                criterion.criterion_id.value,
                str(criterion.executed).lower(),
                str(criterion.observed).lower(),
                str(criterion.evidence_count),
                criterion.source_surface,
                criterion.message,
            )
        )
        for criterion in report.criteria
    )
    return "\n".join(lines)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _source_path_from_descriptor(
    descriptor: PublicBenchmarkDescriptor,
    *,
    schema_id: str,
) -> Path:
    for source in descriptor.source_files:
        if source.schema_id == schema_id:
            return _repo_root() / source.repo_relative_path
    raise ValueError(
        f"public benchmark descriptor '{descriptor.dataset_id}' does not declare schema_id "
        f"{schema_id!r}"
    )


def _criterion(
    *,
    criterion_id: WeakEvidenceCriterionId,
    executed: bool,
    evidence_count: int,
    source_surface: str,
    message: str,
) -> WeakEvidenceBenchmarkCriterion:
    return WeakEvidenceBenchmarkCriterion(
        criterion_id=criterion_id,
        executed=executed,
        observed=evidence_count > 0,
        evidence_count=evidence_count,
        source_surface=source_surface,
        message=message,
    )


def _verified_count(
    report: PublicBenchmarkRunReport | None,
    metric_id: str,
) -> int:
    if report is None:
        return 0
    observed = report.verified_counts.get(metric_id, 0)
    return observed if isinstance(observed, int) and observed >= 0 else 0


def _refused_claim_count(report: PublicBenchmarkRunReport | None) -> int:
    if report is None:
        return 0
    path = Path(report.output_dir) / "biological_rejected_claims.tsv"
    return _count_tsv_rows(path)


def _load_refused_claim_entries(
    report: PublicBenchmarkRunReport | None,
) -> tuple[WeakEvidenceRefusedClaimEntry, ...]:
    if report is None:
        return ()
    path = Path(report.output_dir) / "biological_rejected_claims.tsv"
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as handle:
        rows = tuple(dict(row) for row in csv.DictReader(handle, delimiter="\t"))
    return tuple(
        WeakEvidenceRefusedClaimEntry(
            claim_id=row["claim_id"],
            subject_id=row["subject_id"],
            subject_label=row["subject_label"],
            claim_text=row["claim_text"],
            reason_codes=tuple(
                reason for reason in row.get("reason_codes", "").split(";") if reason
            ),
            validation_note=row["validation_note"],
            source_surface="workflow.pipelines.public_benchmark_runner:lfq_sparse_contrast_benchmark_dataset",
        )
        for row in rows
    )


def _build_refused_claim_study_result(
    *,
    report: PublicBenchmarkRunReport | None,
    refused_claims: tuple[WeakEvidenceRefusedClaimEntry, ...],
) -> ProteomicsStudyResult | None:
    if report is None or report.workflow_result is None or not refused_claims:
        return None
    workflow_report = report.workflow_result.report
    if not isinstance(workflow_report, BiologicalResultReportBundle):
        return None
    study_result = build_proteomics_study_result_from_biological_report_bundle(
        workflow_report
    )
    conclusions = list(study_result.biological_conclusions)
    conclusions.extend(
        ProteomicsStudyConclusionEntry(
            conclusion_id=entry.claim_id,
            kind=ProteomicsStudyConclusionKind.REFUSED_CLAIM,
            subject_id=entry.subject_id,
            subject_label=entry.subject_label,
            status="refused",
            score=None,
            evidence_surface=entry.source_surface,
            summary_text=entry.claim_text,
        )
        for entry in refused_claims
    )
    sorted_conclusions = tuple(
        sorted(
            conclusions,
            key=lambda entry: (entry.kind.value, entry.subject_id, entry.conclusion_id),
        )
    )
    return study_result.model_copy(
        update={
            "biological_conclusions": sorted_conclusions,
            "summary": ProteomicsStudyResultSummary(
                design_entry_count=study_result.summary.design_entry_count,
                matrix_surface_count=study_result.summary.matrix_surface_count,
                statistic_surface_count=study_result.summary.statistic_surface_count,
                qc_surface_count=study_result.summary.qc_surface_count,
                card_surface_count=study_result.summary.card_surface_count,
                conclusion_count=len(sorted_conclusions),
            ),
        }
    )


def _blocked_or_invalid_contrast_count(report: PublicBenchmarkRunReport | None) -> int:
    if report is None:
        return 0
    return _verified_count(report, "cohort_blocked_stratum_count") + _verified_count(
        report, "invalid_section_count"
    )


def _count_tsv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


__all__ = [
    "WeakEvidenceBenchmarkCriterion",
    "WeakEvidenceBenchmarkDescriptor",
    "WeakEvidenceBenchmarkReport",
    "WeakEvidenceRefusedClaimEntry",
    "WeakEvidenceReportSection",
    "WeakEvidenceReportSectionKey",
    "WeakEvidenceBenchmarkStatus",
    "WeakEvidenceBenchmarkSummary",
    "WeakEvidenceCriterionId",
    "build_flagship_weak_evidence_benchmark_descriptor",
    "render_weak_evidence_benchmark_criteria_tsv",
    "render_weak_evidence_benchmark_summary_tsv",
    "run_weak_evidence_benchmark",
]
