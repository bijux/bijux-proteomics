# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced TMT workflow execution over governed review surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.isotope_labeling.validation import TmtValidationReport
from bijux_proteomics.multiplex import (
    TmtInterferenceObservationEntry,
    TmtNormalizationMethod,
    TmtPeptideRatioEntry,
    TmtRatioReport,
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    render_tmt_peptide_ratio_tsv,
)
from bijux_proteomics.quantification import LabelBasedChannelRole, NormalizationMethod
from bijux_proteomics.workflow.exports.artifact_layout import (
    synchronize_workflow_artifact_layout,
)
from bijux_proteomics.workflow.pipelines.advanced_workflow_family import (
    AdvancedWorkflowFamilyArtifactContract,
    AdvancedWorkflowFamilyContract,
    build_advanced_workflow_family_contract,
)
from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
    TmtExperimentWorkflowExportManifest,
    build_tmt_experiment_workflow_bundle,
    write_tmt_experiment_workflow_bundle,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    RejectedEvidenceEntry,
    ResultWarningEntry,
    artifact_name_map,
    build_rejected_evidence_entries_from_issue_rows,
    build_rejected_evidence_entry,
    build_result_warning,
    render_result_rejected_evidence_tsv,
)
from bijux_proteomics_foundation import JsonModel


class AdvancedTmtWorkflowConfig(JsonModel):
    """Config for the advanced TMT workflow owner."""

    model_config = ConfigDict(extra="forbid")

    result_tsv_path: Path
    design_tsv_path: Path
    output_dir: Path
    control_channel: str = Field(..., min_length=1)
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.MAXQUANT
    mapping: TmtReporterColumnMapping | None = None
    channel_columns: tuple[TmtReporterChannelColumn, ...] = Field(default_factory=tuple)
    channel_normalization_method: TmtNormalizationMethod = TmtNormalizationMethod.MEDIAN
    differential_normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    batch_field: str = "batch"
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)
    pairing_field: str | None = None


class AdvancedTmtPeptideDisposition(StrEnum):
    """How one peptide ratio survives interference-aware advanced TMT review."""

    RETAINED = "retained"
    DOWNGRADED_BY_INTERFERENCE = "downgraded_by_interference"
    EXCLUDED_DUE_TO_INTERFERENCE = "excluded_due_to_interference"
    MISSING_RATIO = "missing_ratio"


class AdvancedTmtProteinConfidenceStatus(StrEnum):
    """Protein-level confidence state after interference-aware TMT review."""

    SUPPORTED = "supported"
    DOWNGRADED_BY_INTERFERENCE = "downgraded_by_interference"
    EXCLUDED_DUE_TO_INTERFERENCE = "excluded_due_to_interference"


class AdvancedTmtCompressionStatus(StrEnum):
    """Whether peptide interference suggests ratio compression at the protein level."""

    NOT_DETECTED = "not_detected"
    POSSIBLE_INTERFERENCE_COMPRESSION = "possible_interference_compression"
    MIXED_INTERFERENCE_WITHOUT_CLEAR_COMPRESSION = (
        "mixed_interference_without_clear_compression"
    )
    NOT_ASSESSABLE_ALL_SUPPORT_FLAGGED = "not_assessable_all_support_flagged"
    NOT_ASSESSABLE_MISSING_SAMPLE_RATIOS = "not_assessable_missing_sample_ratios"


class AdvancedTmtWorkflowSummary(JsonModel):
    """Compact summary over one advanced TMT workflow run."""

    model_config = ConfigDict(extra="forbid")

    accepted_input_row_count: int = Field(..., ge=0)
    rejected_input_row_count: int = Field(..., ge=0)
    mapped_channel_count: int = Field(..., ge=0)
    weak_channel_count: int = Field(..., ge=0)
    peptide_ratio_count: int = Field(..., ge=0)
    sample_peptide_ratio_count: int = Field(..., ge=0)
    high_interference_peptide_count: int = Field(..., ge=0)
    excluded_peptide_count: int = Field(..., ge=0)
    protein_ratio_count: int = Field(..., ge=0)
    differential_result_count: int = Field(..., ge=0)
    downgraded_protein_count: int = Field(..., ge=0)
    excluded_protein_count: int = Field(..., ge=0)
    compression_risk_count: int = Field(..., ge=0)
    evidence_card_count: int = Field(..., ge=0)


class AdvancedTmtWorkflowArtifactPaths(JsonModel):
    """Advanced TMT artifact paths written into the output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    tmt_workflow_manifest_json: str = Field(..., min_length=1)
    label_based_report_manifest_json: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    reporter_import_summary_tsv: str = Field(..., min_length=1)
    normalization_summary_tsv: str = Field(..., min_length=1)
    validation_summary_tsv: str = Field(..., min_length=1)
    peptide_ratio_tsv: str = Field(..., min_length=1)
    protein_ratio_tsv: str = Field(..., min_length=1)
    differential_results_tsv: str = Field(..., min_length=1)
    filtered_interference_tsv: str = Field(..., min_length=1)
    validation_weak_tsv: str = Field(..., min_length=1)
    peptide_confidence_tsv: str = Field(..., min_length=1)
    protein_compression_tsv: str = Field(..., min_length=1)
    evidence_card_tsv: str = Field(..., min_length=1)


class AdvancedTmtWorkflowManifest(JsonModel):
    """Stable manifest over one advanced TMT workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    summary: AdvancedTmtWorkflowSummary
    artifacts: AdvancedTmtWorkflowArtifactPaths
    tmt_workflow_manifest: TmtExperimentWorkflowExportManifest
    family_protocol: AdvancedWorkflowFamilyContract
    note: str = Field(..., min_length=1)


class AdvancedTmtPeptideConfidenceEntry(JsonModel):
    """One sample-facing peptide ratio with interference-aware disposition."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    numerator_channel: str = Field(..., min_length=1)
    numerator_sample_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    ratio: float | None = Field(default=None, ge=0.0)
    log2_ratio: float | None = None
    isolation_interference_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    high_interference: bool
    disposition: AdvancedTmtPeptideDisposition
    note: str = Field(..., min_length=1)


class AdvancedTmtProteinCompressionEntry(JsonModel):
    """One protein-level compression review derived from peptide interference context."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    clean_sample_peptide_count: int = Field(..., ge=0)
    flagged_sample_peptide_count: int = Field(..., ge=0)
    clean_median_abs_log2_ratio: float | None = Field(default=None, ge=0.0)
    flagged_median_abs_log2_ratio: float | None = Field(default=None, ge=0.0)
    protein_median_abs_log2_ratio: float | None = Field(default=None, ge=0.0)
    attenuation_delta: float | None = None
    compression_status: AdvancedTmtCompressionStatus
    note: str = Field(..., min_length=1)


class AdvancedTmtEvidenceCard(JsonModel):
    """One protein-level advanced TMT evidence card with interference-aware confidence."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    confidence_status: AdvancedTmtProteinConfidenceStatus
    supporting_clean_peptide_count: int = Field(..., ge=0)
    flagged_peptide_count: int = Field(..., ge=0)
    excluded_peptide_count: int = Field(..., ge=0)
    compression_status: AdvancedTmtCompressionStatus
    differential_log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class AdvancedTmtWorkflowReport(BiologyResult):
    """Advanced TMT workflow report with interference-aware confidence review."""

    model_config = ConfigDict(extra="forbid")

    tmt_workflow: TmtExperimentWorkflowBundle
    tmt_workflow_manifest: TmtExperimentWorkflowExportManifest
    peptide_confidence_entries: tuple[AdvancedTmtPeptideConfidenceEntry, ...] = Field(
        default_factory=tuple
    )
    protein_compression_entries: tuple[AdvancedTmtProteinCompressionEntry, ...] = Field(
        default_factory=tuple
    )
    evidence_cards: tuple[AdvancedTmtEvidenceCard, ...] = Field(default_factory=tuple)
    summary: AdvancedTmtWorkflowSummary
    manifest: AdvancedTmtWorkflowManifest
    family_protocol: AdvancedWorkflowFamilyContract
    note: str = Field(..., min_length=1)


def run_advanced_tmt_workflow(
    config: AdvancedTmtWorkflowConfig,
) -> AdvancedTmtWorkflowReport:
    """Run the advanced TMT workflow and write one durable review directory."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    base_report = build_tmt_experiment_workflow_bundle(
        config.result_tsv_path,
        config.design_tsv_path,
        control_channel=config.control_channel,
        source_kind=config.source_kind,
        mapping=config.mapping,
        channel_columns=config.channel_columns,
        channel_normalization_method=config.channel_normalization_method,
        differential_normalization_method=config.differential_normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        batch_field=config.batch_field,
        covariate_fields=tuple(dict.fromkeys(config.covariate_fields)),
        pairing_field=config.pairing_field,
    )
    workflow_manifest = write_tmt_experiment_workflow_bundle(base_report, output_dir)
    workflow_manifest_path = output_dir / "tmt_experiment_workflow_manifest.json"
    atomic_write_text(
        workflow_manifest_path,
        workflow_manifest.to_stable_json() + "\n",
    )

    ratio_report = _require_tmt_ratio_report(base_report)
    validation_report = _require_tmt_validation_report(base_report)
    differential_report = (
        base_report.report.differential_analysis_report.differential_abundance_report
    )
    if differential_report is None:
        raise ValueError(
            "advanced tmt workflow requires differential abundance results"
        )
    label_manifest = workflow_manifest.label_based_report_manifest

    peptide_confidence_entries = _build_peptide_confidence_entries(base_report)
    protein_compression_entries = _build_protein_compression_entries(
        base_report,
        peptide_confidence_entries=peptide_confidence_entries,
    )
    evidence_cards = _build_evidence_cards(
        base_report,
        peptide_confidence_entries=peptide_confidence_entries,
        compression_entries=protein_compression_entries,
    )

    peptide_ratio_name = "advanced_tmt_peptide_ratios.tsv"
    peptide_confidence_name = "advanced_tmt_peptide_confidence.tsv"
    protein_compression_name = "advanced_tmt_protein_compression.tsv"
    evidence_card_name = "advanced_tmt_evidence_cards.tsv"
    rejected_evidence_name = "rejected_evidence.tsv"
    summary_name = "advanced_tmt_summary.tsv"

    write_output_table_tsv(
        (output_dir / peptide_ratio_name), render_tmt_peptide_ratio_tsv(ratio_report)
    )
    write_output_table_tsv(
        (output_dir / peptide_confidence_name),
        render_advanced_tmt_peptide_confidence_tsv(peptide_confidence_entries),
    )
    write_output_table_tsv(
        (output_dir / protein_compression_name),
        render_advanced_tmt_protein_compression_tsv(protein_compression_entries),
    )
    write_output_table_tsv(
        (output_dir / evidence_card_name),
        render_advanced_tmt_evidence_cards_tsv(evidence_cards),
    )
    write_output_table_tsv(
        (output_dir / rejected_evidence_name),
        render_result_rejected_evidence_tsv(
            _build_advanced_tmt_rejected_evidence(
                report=base_report,
                evidence_cards=evidence_cards,
                related_artifact=rejected_evidence_name,
            )
        ),
    )

    summary = AdvancedTmtWorkflowSummary(
        accepted_input_row_count=base_report.summary.accepted_input_row_count,
        rejected_input_row_count=base_report.summary.rejected_input_row_count,
        mapped_channel_count=base_report.summary.mapped_channel_count,
        weak_channel_count=validation_report.summary.weak_channel_count,
        peptide_ratio_count=ratio_report.summary.peptide_ratio_count,
        sample_peptide_ratio_count=len(
            [
                entry
                for entry in peptide_confidence_entries
                if entry.disposition is not AdvancedTmtPeptideDisposition.MISSING_RATIO
            ]
        ),
        high_interference_peptide_count=len(
            [entry for entry in peptide_confidence_entries if entry.high_interference]
        ),
        excluded_peptide_count=len(
            [
                entry
                for entry in peptide_confidence_entries
                if entry.disposition
                is AdvancedTmtPeptideDisposition.EXCLUDED_DUE_TO_INTERFERENCE
            ]
        ),
        protein_ratio_count=ratio_report.summary.protein_ratio_count,
        differential_result_count=len(differential_report.entries),
        downgraded_protein_count=len(
            [
                card
                for card in evidence_cards
                if card.confidence_status
                is AdvancedTmtProteinConfidenceStatus.DOWNGRADED_BY_INTERFERENCE
            ]
        ),
        excluded_protein_count=len(
            [
                card
                for card in evidence_cards
                if card.confidence_status
                is AdvancedTmtProteinConfidenceStatus.EXCLUDED_DUE_TO_INTERFERENCE
            ]
        ),
        compression_risk_count=len(
            [
                entry
                for entry in protein_compression_entries
                if entry.compression_status
                is AdvancedTmtCompressionStatus.POSSIBLE_INTERFERENCE_COMPRESSION
            ]
        ),
        evidence_card_count=len(evidence_cards),
    )
    write_output_table_tsv(
        (output_dir / summary_name), render_advanced_tmt_workflow_summary_tsv(summary)
    )

    workflow_manifest_name = "advanced_tmt_workflow_manifest.json"
    family_protocol = build_advanced_workflow_family_contract(
        workflow_name="advanced_tmt",
        config=config,
        primary_input_fields=("result_tsv_path",),
        design_input_fields=("design_tsv_path",),
        reference_input_fields=(
            "control_channel",
            "mapping",
            "channel_columns",
            "batch_field",
            "covariate_fields",
            "pairing_field",
        ),
        comparison_input_fields=("condition_a", "condition_b"),
        artifacts=AdvancedWorkflowFamilyArtifactContract(
            workflow_manifest_json=workflow_manifest_name,
            base_workflow_manifest_json=workflow_manifest_path.name,
            review_manifest_json=workflow_manifest.artifacts.label_based_report_manifest_json,
            summary_tsv=summary_name,
            rejected_evidence_tsv=rejected_evidence_name,
        ),
        note=(
            "advanced tmt workflow follows the canonical advanced workflow family "
            "through normalized config categories plus shared summary, manifest, "
            "and rejected-evidence output roles"
        ),
    )

    manifest = AdvancedTmtWorkflowManifest(
        summary=summary,
        artifacts=AdvancedTmtWorkflowArtifactPaths(
            summary_tsv=summary_name,
            tmt_workflow_manifest_json=workflow_manifest_path.name,
            label_based_report_manifest_json=workflow_manifest.artifacts.label_based_report_manifest_json,
            rejected_evidence_tsv=rejected_evidence_name,
            reporter_import_summary_tsv=workflow_manifest.artifacts.reporter_import_summary_tsv,
            normalization_summary_tsv=_required_artifact_name(
                label_manifest.artifacts.tmt_normalization_summary_tsv,
                artifact_name="tmt_normalization_summary_tsv",
            ),
            validation_summary_tsv=_required_artifact_name(
                label_manifest.artifacts.tmt_validation_summary_tsv,
                artifact_name="tmt_validation_summary_tsv",
            ),
            peptide_ratio_tsv=peptide_ratio_name,
            protein_ratio_tsv=_required_artifact_name(
                label_manifest.artifacts.tmt_protein_ratio_tsv,
                artifact_name="tmt_protein_ratio_tsv",
            ),
            differential_results_tsv=label_manifest.artifacts.differential_results_tsv,
            filtered_interference_tsv=workflow_manifest.artifacts.filtered_interference_tsv,
            validation_weak_tsv=_required_artifact_name(
                label_manifest.artifacts.tmt_validation_weak_tsv,
                artifact_name="tmt_validation_weak_tsv",
            ),
            peptide_confidence_tsv=peptide_confidence_name,
            protein_compression_tsv=protein_compression_name,
            evidence_card_tsv=evidence_card_name,
        ),
        tmt_workflow_manifest=workflow_manifest,
        family_protocol=family_protocol,
        note=(
            "advanced tmt workflow preserves governed reporter import, channel validation, "
            "normalization, ratio analysis, protein differential results, and one "
            "interference-aware confidence layer where high-interference peptides "
            "downgrade or exclude downstream protein interpretation"
        ),
    )
    manifest_path = output_dir / workflow_manifest_name
    atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="run_advanced_tmt_workflow",
    )

    return AdvancedTmtWorkflowReport(
        tmt_workflow=base_report,
        tmt_workflow_manifest=workflow_manifest,
        peptide_confidence_entries=peptide_confidence_entries,
        protein_compression_entries=protein_compression_entries,
        evidence_cards=evidence_cards,
        summary=summary,
        manifest=manifest,
        family_protocol=family_protocol,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_advanced_tmt_warnings(summary=summary, manifest=manifest),
        rejected_evidence=_build_advanced_tmt_rejected_evidence(
            report=base_report,
            evidence_cards=evidence_cards,
            related_artifact=manifest.artifacts.rejected_evidence_tsv,
        ),
        note=(
            "advanced tmt workflow composes governed reporter import, channel validation, "
            "normalization, interference review, ratio analysis, protein differential, "
            "compression review, and evidence cards without letting high-interference "
            "peptides pass as unchanged confident support"
        ),
    )


def render_advanced_tmt_workflow_summary_tsv(
    summary: AdvancedTmtWorkflowSummary,
) -> str:
    """Render one advanced TMT workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("accepted_input_row_count", summary.accepted_input_row_count),
        ("rejected_input_row_count", summary.rejected_input_row_count),
        ("mapped_channel_count", summary.mapped_channel_count),
        ("weak_channel_count", summary.weak_channel_count),
        ("peptide_ratio_count", summary.peptide_ratio_count),
        ("sample_peptide_ratio_count", summary.sample_peptide_ratio_count),
        ("high_interference_peptide_count", summary.high_interference_peptide_count),
        ("excluded_peptide_count", summary.excluded_peptide_count),
        ("protein_ratio_count", summary.protein_ratio_count),
        ("differential_result_count", summary.differential_result_count),
        ("downgraded_protein_count", summary.downgraded_protein_count),
        ("excluded_protein_count", summary.excluded_protein_count),
        ("compression_risk_count", summary.compression_risk_count),
        ("evidence_card_count", summary.evidence_card_count),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_advanced_tmt_peptide_confidence_tsv(
    entries: tuple[AdvancedTmtPeptideConfidenceEntry, ...],
) -> str:
    """Render interference-aware peptide confidence rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "multiplex_group",
            "numerator_channel",
            "numerator_sample_id",
            "protein_id",
            "peptide_sequence",
            "ratio",
            "log2_ratio",
            "isolation_interference_fraction",
            "high_interference",
            "disposition",
            "note",
        )
    )
    for entry in sort_rows_by_fields(
        entries,
        "protein_id",
        "peptide_sequence",
        "multiplex_group",
        "numerator_channel",
    ):
        writer.writerow(
            (
                entry.multiplex_group,
                entry.numerator_channel,
                entry.numerator_sample_id,
                entry.protein_id,
                entry.peptide_sequence,
                "" if entry.ratio is None else f"{entry.ratio:g}",
                "" if entry.log2_ratio is None else f"{entry.log2_ratio:g}",
                (
                    ""
                    if entry.isolation_interference_fraction is None
                    else f"{entry.isolation_interference_fraction:g}"
                ),
                str(entry.high_interference).lower(),
                entry.disposition.value,
                entry.note,
            )
        )
    return handle.getvalue()


def render_advanced_tmt_protein_compression_tsv(
    entries: tuple[AdvancedTmtProteinCompressionEntry, ...],
) -> str:
    """Render protein-level compression review rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "representative_protein_ref",
            "clean_sample_peptide_count",
            "flagged_sample_peptide_count",
            "clean_median_abs_log2_ratio",
            "flagged_median_abs_log2_ratio",
            "protein_median_abs_log2_ratio",
            "attenuation_delta",
            "compression_status",
            "note",
        )
    )
    for entry in sort_rows_by_fields(entries, "protein_id"):
        writer.writerow(
            (
                entry.protein_id,
                entry.representative_protein_ref,
                entry.clean_sample_peptide_count,
                entry.flagged_sample_peptide_count,
                (
                    ""
                    if entry.clean_median_abs_log2_ratio is None
                    else f"{entry.clean_median_abs_log2_ratio:g}"
                ),
                (
                    ""
                    if entry.flagged_median_abs_log2_ratio is None
                    else f"{entry.flagged_median_abs_log2_ratio:g}"
                ),
                (
                    ""
                    if entry.protein_median_abs_log2_ratio is None
                    else f"{entry.protein_median_abs_log2_ratio:g}"
                ),
                ""
                if entry.attenuation_delta is None
                else f"{entry.attenuation_delta:g}",
                entry.compression_status.value,
                entry.note,
            )
        )
    return handle.getvalue()


def render_advanced_tmt_evidence_cards_tsv(
    entries: tuple[AdvancedTmtEvidenceCard, ...],
) -> str:
    """Render protein-level advanced TMT evidence cards as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "representative_protein_ref",
            "confidence_status",
            "supporting_clean_peptide_count",
            "flagged_peptide_count",
            "excluded_peptide_count",
            "compression_status",
            "differential_log2_fold_change",
            "adjusted_p_value",
            "note",
        )
    )
    for entry in sort_rows_by_fields(entries, "protein_id"):
        writer.writerow(
            (
                entry.protein_id,
                entry.representative_protein_ref,
                entry.confidence_status.value,
                entry.supporting_clean_peptide_count,
                entry.flagged_peptide_count,
                entry.excluded_peptide_count,
                entry.compression_status.value,
                f"{entry.differential_log2_fold_change:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                entry.note,
            )
        )
    return handle.getvalue()


def _build_advanced_tmt_warnings(
    *,
    summary: AdvancedTmtWorkflowSummary,
    manifest: AdvancedTmtWorkflowManifest,
) -> tuple[ResultWarningEntry, ...]:
    warnings: list[ResultWarningEntry] = []
    if summary.rejected_input_row_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_tmt:rejected_input_rows",
                warning_code="rejected_input_row_present",
                source_surface="advanced_tmt_workflow",
                message=(
                    f"advanced TMT rejected {summary.rejected_input_row_count} reporter rows "
                    "during import"
                ),
                related_artifact=manifest.artifacts.reporter_import_summary_tsv,
            )
        )
    if summary.high_interference_peptide_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_tmt:high_interference",
                warning_code="high_interference_peptide_present",
                source_surface="advanced_tmt_workflow",
                message=(
                    f"advanced TMT flagged {summary.high_interference_peptide_count} peptide ratios "
                    "for high interference"
                ),
                related_artifact=manifest.artifacts.filtered_interference_tsv,
            )
        )
    if summary.excluded_protein_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_tmt:excluded_proteins",
                warning_code="excluded_protein_due_to_interference",
                source_surface="advanced_tmt_workflow",
                message=(
                    f"advanced TMT excluded {summary.excluded_protein_count} proteins because "
                    "their support was interference-only"
                ),
                related_artifact=manifest.artifacts.evidence_card_tsv,
            )
        )
    return tuple(warnings)


def _build_advanced_tmt_rejected_evidence(
    *,
    report: TmtExperimentWorkflowBundle,
    evidence_cards: tuple[AdvancedTmtEvidenceCard, ...],
    related_artifact: str,
) -> tuple[RejectedEvidenceEntry, ...]:
    matrix_report = report.report.tmt_matrix_report
    if matrix_report is None:
        raise ValueError("advanced tmt workflow requires a TMT matrix report")
    return build_rejected_evidence_entries_from_issue_rows(
        matrix_report.source_report.rejected_rows,
        source_surface="advanced_tmt_workflow",
        related_artifact=related_artifact,
        entity_prefix="reporter_row",
        entity_type="reporter_row",
    ) + tuple(
        build_rejected_evidence_entry(
            evidence_id=f"advanced_tmt:{card.protein_id}",
            source_surface="advanced_tmt_workflow",
            reason_code=card.confidence_status.value,
            message=card.note,
            related_artifact=related_artifact,
            entity_type="protein",
            entity_id=card.protein_id,
        )
        for card in evidence_cards
        if card.confidence_status
        is AdvancedTmtProteinConfidenceStatus.EXCLUDED_DUE_TO_INTERFERENCE
    )


def _require_tmt_ratio_report(
    base_report: TmtExperimentWorkflowBundle,
) -> TmtRatioReport:
    ratio_report = base_report.report.tmt_ratio_report
    if ratio_report is None:
        raise ValueError("advanced tmt workflow requires protein and peptide ratios")
    return ratio_report


def _require_tmt_validation_report(
    base_report: TmtExperimentWorkflowBundle,
) -> TmtValidationReport:
    validation_report = base_report.report.tmt_validation_report
    if validation_report is None:
        raise ValueError("advanced tmt workflow requires tmt channel validation")
    return validation_report


def _build_peptide_confidence_entries(
    base_report: TmtExperimentWorkflowBundle,
) -> tuple[AdvancedTmtPeptideConfidenceEntry, ...]:
    ratio_report = _require_tmt_ratio_report(base_report)
    observations = base_report.interference_report.observations
    clean_support_by_protein: dict[str, int] = {}

    for entry in ratio_report.peptide_ratios:
        if entry.numerator_role is not LabelBasedChannelRole.SAMPLE:
            continue
        protein_id = _representative_protein_ref(
            entry.protein_refs, fallback=entry.peptide_id
        )
        matching = _matching_interference_observations(entry, observations)
        high_interference = any(
            observation.threshold_exceeded for observation in matching
        )
        if entry.missing_reason is None and not high_interference:
            clean_support_by_protein[protein_id] = (
                clean_support_by_protein.get(protein_id, 0) + 1
            )

    entries: list[AdvancedTmtPeptideConfidenceEntry] = []
    for ratio_entry in ratio_report.peptide_ratios:
        if ratio_entry.numerator_role is not LabelBasedChannelRole.SAMPLE:
            continue
        protein_id = _representative_protein_ref(
            ratio_entry.protein_refs,
            fallback=ratio_entry.peptide_id,
        )
        matching = _matching_interference_observations(ratio_entry, observations)
        fractions = [
            observation.isolation_interference_fraction
            for observation in matching
            if observation.isolation_interference_fraction is not None
        ]
        max_fraction = None if not fractions else max(fractions)
        high_interference = any(
            observation.threshold_exceeded for observation in matching
        )
        if ratio_entry.missing_reason is not None:
            disposition = AdvancedTmtPeptideDisposition.MISSING_RATIO
            note = "sample ratio is missing before interference-aware confidence review"
        elif high_interference and clean_support_by_protein.get(protein_id, 0) == 0:
            disposition = AdvancedTmtPeptideDisposition.EXCLUDED_DUE_TO_INTERFERENCE
            note = "high interference dominates the available sample peptide support for this protein, so the peptide is excluded from confident downstream support"
        elif high_interference:
            disposition = AdvancedTmtPeptideDisposition.DOWNGRADED_BY_INTERFERENCE
            note = "high interference is preserved, but clean peptide support still exists for the same protein so the peptide only downgrades confidence"
        else:
            disposition = AdvancedTmtPeptideDisposition.RETAINED
            note = "sample peptide ratio stays in confident support because interference remains below threshold"
        entries.append(
            AdvancedTmtPeptideConfidenceEntry(
                multiplex_group=ratio_entry.multiplex_group,
                numerator_channel=ratio_entry.numerator_channel,
                numerator_sample_id=ratio_entry.numerator_sample_id,
                protein_id=protein_id,
                peptide_sequence=ratio_entry.peptide_sequence,
                ratio=ratio_entry.ratio,
                log2_ratio=ratio_entry.log2_ratio,
                isolation_interference_fraction=max_fraction,
                high_interference=high_interference,
                disposition=disposition,
                note=note,
            )
        )
    return tuple(
        sort_rows_by_fields(
            tuple(entries),
            "protein_id",
            "peptide_sequence",
            "multiplex_group",
            "numerator_channel",
        )
    )


def _build_protein_compression_entries(
    base_report: TmtExperimentWorkflowBundle,
    *,
    peptide_confidence_entries: tuple[AdvancedTmtPeptideConfidenceEntry, ...],
) -> tuple[AdvancedTmtProteinCompressionEntry, ...]:
    ratio_report = _require_tmt_ratio_report(base_report)
    protein_ratio_by_id: dict[str, list[float]] = {}
    for protein_ratio_entry in ratio_report.protein_ratios:
        if (
            protein_ratio_entry.numerator_role is LabelBasedChannelRole.SAMPLE
            and protein_ratio_entry.log2_ratio is not None
            and protein_ratio_entry.missing_reason is None
        ):
            protein_ratio_by_id.setdefault(protein_ratio_entry.protein_id, []).append(
                abs(protein_ratio_entry.log2_ratio)
            )

    peptide_by_protein: dict[str, list[AdvancedTmtPeptideConfidenceEntry]] = {}
    for peptide_entry in peptide_confidence_entries:
        if peptide_entry.disposition is AdvancedTmtPeptideDisposition.MISSING_RATIO:
            continue
        peptide_by_protein.setdefault(peptide_entry.protein_id, []).append(
            peptide_entry
        )

    entries: list[AdvancedTmtProteinCompressionEntry] = []
    for protein_id in sorted(peptide_by_protein):
        protein_entries = peptide_by_protein[protein_id]
        clean = [
            abs(entry.log2_ratio)
            for entry in protein_entries
            if entry.log2_ratio is not None and not entry.high_interference
        ]
        flagged = [
            abs(entry.log2_ratio)
            for entry in protein_entries
            if entry.log2_ratio is not None and entry.high_interference
        ]
        protein_values = protein_ratio_by_id.get(protein_id, [])
        representative_protein_ref = _representative_protein_ref(
            (protein_id,), fallback=protein_id
        )
        clean_median = None if not clean else float(median(clean))
        flagged_median = None if not flagged else float(median(flagged))
        protein_median = None if not protein_values else float(median(protein_values))
        attenuation_delta = (
            None
            if clean_median is None or protein_median is None
            else round(clean_median - protein_median, 6)
        )
        if flagged and not clean:
            status = AdvancedTmtCompressionStatus.NOT_ASSESSABLE_ALL_SUPPORT_FLAGGED
            note = "all observed sample peptide support is high interference, so ratio compression cannot be isolated from general support loss"
        elif not protein_values or clean_median is None:
            status = AdvancedTmtCompressionStatus.NOT_ASSESSABLE_MISSING_SAMPLE_RATIOS
            note = "sample protein ratios or clean peptide ratios are missing, so compression review cannot be computed"
        elif not flagged:
            status = AdvancedTmtCompressionStatus.NOT_DETECTED
            note = "no high-interference sample peptide support is present for this protein"
        elif attenuation_delta is not None and attenuation_delta > 0.25:
            status = AdvancedTmtCompressionStatus.POSSIBLE_INTERFERENCE_COMPRESSION
            note = "clean peptide ratios remain stronger than the aggregated protein ratio, which is consistent with interference-driven ratio compression"
        else:
            status = AdvancedTmtCompressionStatus.MIXED_INTERFERENCE_WITHOUT_CLEAR_COMPRESSION
            note = "high-interference peptide support is present, but the observed protein ratio attenuation does not cross the compression trigger"
        entries.append(
            AdvancedTmtProteinCompressionEntry(
                protein_id=protein_id,
                representative_protein_ref=representative_protein_ref,
                clean_sample_peptide_count=len(clean),
                flagged_sample_peptide_count=len(flagged),
                clean_median_abs_log2_ratio=clean_median,
                flagged_median_abs_log2_ratio=flagged_median,
                protein_median_abs_log2_ratio=protein_median,
                attenuation_delta=attenuation_delta,
                compression_status=status,
                note=note,
            )
        )
    return tuple(sort_rows_by_fields(tuple(entries), "protein_id"))


def _build_evidence_cards(
    base_report: TmtExperimentWorkflowBundle,
    *,
    peptide_confidence_entries: tuple[AdvancedTmtPeptideConfidenceEntry, ...],
    compression_entries: tuple[AdvancedTmtProteinCompressionEntry, ...],
) -> tuple[AdvancedTmtEvidenceCard, ...]:
    differential_report = (
        base_report.report.differential_analysis_report.differential_abundance_report
    )
    if differential_report is None:
        raise ValueError(
            "advanced tmt workflow requires differential abundance results"
        )
    compression_by_protein = {entry.protein_id: entry for entry in compression_entries}
    peptide_by_protein: dict[str, list[AdvancedTmtPeptideConfidenceEntry]] = {}
    for entry in peptide_confidence_entries:
        peptide_by_protein.setdefault(entry.protein_id, []).append(entry)

    cards: list[AdvancedTmtEvidenceCard] = []
    for differential_entry in differential_report.entries:
        protein_id = differential_entry.entity_id
        peptide_entries = peptide_by_protein.get(protein_id, [])
        clean_count = sum(1 for entry in peptide_entries if not entry.high_interference)
        flagged_count = sum(1 for entry in peptide_entries if entry.high_interference)
        excluded_count = sum(
            1
            for entry in peptide_entries
            if entry.disposition
            is AdvancedTmtPeptideDisposition.EXCLUDED_DUE_TO_INTERFERENCE
        )
        if flagged_count > 0 and clean_count == 0:
            confidence_status = (
                AdvancedTmtProteinConfidenceStatus.EXCLUDED_DUE_TO_INTERFERENCE
            )
            note = "all observed sample peptide support crosses the interference threshold, so the protein result is excluded from confident interpretation"
        elif flagged_count > 0:
            confidence_status = (
                AdvancedTmtProteinConfidenceStatus.DOWNGRADED_BY_INTERFERENCE
            )
            note = "high-interference peptides are present, so the protein result is retained only with downgraded confidence"
        else:
            confidence_status = AdvancedTmtProteinConfidenceStatus.SUPPORTED
            note = "sample peptide support remains below the interference threshold for this protein"
        compression_entry = compression_by_protein.get(
            protein_id,
            AdvancedTmtProteinCompressionEntry(
                protein_id=protein_id,
                representative_protein_ref=protein_id,
                clean_sample_peptide_count=0,
                flagged_sample_peptide_count=0,
                clean_median_abs_log2_ratio=None,
                flagged_median_abs_log2_ratio=None,
                protein_median_abs_log2_ratio=None,
                attenuation_delta=None,
                compression_status=AdvancedTmtCompressionStatus.NOT_ASSESSABLE_MISSING_SAMPLE_RATIOS,
                note="no sample peptide support was available for compression review",
            ),
        )
        cards.append(
            AdvancedTmtEvidenceCard(
                protein_id=protein_id,
                representative_protein_ref=compression_entry.representative_protein_ref,
                confidence_status=confidence_status,
                supporting_clean_peptide_count=clean_count,
                flagged_peptide_count=flagged_count,
                excluded_peptide_count=excluded_count,
                compression_status=compression_entry.compression_status,
                differential_log2_fold_change=differential_entry.log2_fold_change,
                adjusted_p_value=differential_entry.adjusted_p_value,
                note=note,
            )
        )
    return tuple(sort_rows_by_fields(tuple(cards), "protein_id"))


def _matching_interference_observations(
    ratio_entry: TmtPeptideRatioEntry,
    observations: tuple[TmtInterferenceObservationEntry, ...],
) -> tuple[TmtInterferenceObservationEntry, ...]:
    matches: list[TmtInterferenceObservationEntry] = []
    ratio_refs = set(ratio_entry.protein_refs)
    for observation in observations:
        if observation.multiplex_group != ratio_entry.multiplex_group:
            continue
        if observation.multiplex_channel != ratio_entry.numerator_channel:
            continue
        if observation.modified_peptide not in {
            ratio_entry.peptide_id,
            ratio_entry.peptide_sequence,
        }:
            continue
        if ratio_refs and not ratio_refs.intersection(observation.protein_refs):
            continue
        matches.append(observation)
    return tuple(matches)


def _representative_protein_ref(
    protein_refs: tuple[str, ...],
    *,
    fallback: str,
) -> str:
    if protein_refs:
        return sort_strings(protein_refs)[0]
    return fallback


def _required_artifact_name(name: str | None, *, artifact_name: str) -> str:
    if name is None:
        raise ValueError(f"advanced tmt workflow requires {artifact_name}")
    return name


__all__ = [
    "AdvancedTmtCompressionStatus",
    "AdvancedTmtEvidenceCard",
    "AdvancedTmtPeptideConfidenceEntry",
    "AdvancedTmtPeptideDisposition",
    "AdvancedTmtProteinCompressionEntry",
    "AdvancedTmtProteinConfidenceStatus",
    "AdvancedTmtWorkflowArtifactPaths",
    "AdvancedTmtWorkflowConfig",
    "AdvancedTmtWorkflowManifest",
    "AdvancedTmtWorkflowReport",
    "AdvancedTmtWorkflowSummary",
    "render_advanced_tmt_evidence_cards_tsv",
    "render_advanced_tmt_peptide_confidence_tsv",
    "render_advanced_tmt_protein_compression_tsv",
    "render_advanced_tmt_workflow_summary_tsv",
    "run_advanced_tmt_workflow",
]
