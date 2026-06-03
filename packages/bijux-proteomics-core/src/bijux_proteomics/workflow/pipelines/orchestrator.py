# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Core workflow orchestrator over owned proteomics workflow entrypoints."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import TypeAlias, cast

from pydantic import ConfigDict, Field

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics.dia import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
)
from bijux_proteomics.identification import ParsimonyVariant, SearchAdapterKind
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.isotope_labeling import (
    SilacColumnMapping,
    SilacQuantificationPolicy,
)
from bijux_proteomics.multiplex import (
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
)
from bijux_proteomics.multiplex.normalization import TmtNormalizationMethod
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmLocalizationColumnMapping,
    PtmMotifComparisonPolicy,
    PtmMotifRegulationDirection,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    PtmSiteQuantAmbiguityPolicy,
)
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.study import ExperimentDesign, build_experiment_design
from bijux_proteomics.review import VolcanoReviewPolicy
from bijux_proteomics.targeted import (
    TargetedAssayQcReport,
    TargetedMatrixReport,
    TargetedResultImportReport,
    TargetedResultSourceKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
    build_skyline_result_import_report,
    build_targeted_assay_qc_report,
    build_targeted_matrix_report,
    build_transition_table_result_import_report,
)
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    AdvancedTargetedWorkflowManifest,
    TargetedValidationWorkflowConfig,
    TargetedValidationWorkflowReport,
    run_targeted_validation_workflow,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    build_biological_result_report_bundle,
    write_biological_result_report_bundle,
)
from bijux_proteomics.workflow.pipelines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
    DdaBiologicalWorkflowExportManifest,
    DdaPsmAcceptancePolicy,
    build_dda_biological_workflow_bundle,
    write_dda_biological_workflow_bundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
    DiannBiologicalWorkflowExportManifest,
    build_diann_biological_workflow_bundle,
    write_diann_biological_workflow_bundle,
)
from bijux_proteomics.workflow.pipelines.label_based_reporting import (
    LabelBasedReportBundle,
    LabelBasedReportExportManifest,
    build_silac_label_based_report_bundle,
    write_label_based_report_bundle,
)
from bijux_proteomics.workflow.pipelines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
    MaxquantBiologicalWorkflowExportManifest,
    MaxquantProteinGroupAcceptancePolicy,
    build_maxquant_biological_workflow_bundle,
    write_maxquant_biological_workflow_bundle,
)
from bijux_proteomics.workflow.pipelines.ptm_site_workflow import (
    PtmSiteWorkflowBundle,
    PtmSiteWorkflowExportManifest,
    build_ptm_site_workflow_bundle,
    write_ptm_site_workflow_bundle,
)
from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
    TmtExperimentWorkflowExportManifest,
    build_tmt_experiment_workflow_bundle,
    write_tmt_experiment_workflow_bundle,
)
from bijux_proteomics.workflow.targeted_review_workflow import (
    TargetedAssayQcWorkflowExportManifest,
    TargetedMatrixWorkflowExportManifest,
    export_targeted_assay_qc_workflow_artifacts,
    export_targeted_matrix_workflow_artifacts,
)
from bijux_proteomics.workflow.result_types import (
    RejectedEvidenceEntry,
    ResultWarningEntry,
    WorkflowResult as StandardWorkflowResult,
    artifact_name_map,
    build_rejected_evidence_entries_from_issue_rows,
    build_result_warning,
)
from bijux_proteomics_foundation import JsonModel


class WorkflowMode(StrEnum):
    """Owned proteomics workflow modes dispatchable through one API."""

    LABEL_FREE = "label_free"
    DIANN = "diann"
    MAXQUANT = "maxquant"
    FRAGPIPE = "fragpipe"
    GENERIC_PSM = "generic_psm"
    PTM = "ptm"
    TMT = "tmt"
    SILAC = "silac"
    TARGETED = "targeted"


class TargetedWorkflowStage(StrEnum):
    """Targeted review stages dispatchable under the targeted workflow mode."""

    MATRIX = "matrix"
    ASSAY_QC = "assay_qc"
    VALIDATION = "validation"


class WorkflowBaseConfig(JsonModel):
    """Shared orchestration settings across proteomics workflow modes."""

    model_config = ConfigDict(extra="forbid")

    output_dir: Path | None = None


class LabelFreeWorkflowConfig(WorkflowBaseConfig):
    """Config for direct LFQ-to-biology workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.LABEL_FREE
    input_tsv_path: Path
    design_tsv_path: Path
    proteins_fasta_path: Path
    protocol_context_tsv_path: Path | None = None
    annotation_tsv_path: Path | None = None
    context_annotation_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    mapping: Ms1FeatureColumnMapping = Field(
        default_factory=lambda: Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
            protein_separator=";",
        )
    )
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM
    top_n: int = Field(default=3, ge=1)
    chunk_size_rows: int | None = Field(default=None, ge=1)
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy = Field(
        default_factory=VolcanoReviewPolicy
    )


class DdaWorkflowConfig(WorkflowBaseConfig):
    """Config for DDA, generic PSM, and FragPipe workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.GENERIC_PSM
    search_result_tsv_path: Path
    design_tsv_path: Path
    proteins_fasta_path: Path
    protocol_context_tsv_path: Path | None = None
    adapter_kind: SearchAdapterKind = SearchAdapterKind.GENERIC
    generic_mapping_path: Path | None = None
    dialect_id: str = "default"
    source_protein_tsv_path: Path | None = None
    annotation_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    psm_q_value_threshold: float = Field(default=0.01, ge=0.0, le=1.0)
    parsimony_variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM
    top_n: int = Field(default=3, ge=1)
    chunk_size_rows: int | None = Field(default=None, ge=1)
    minimum_shared_peptides: int = Field(default=1, ge=0)
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy = Field(
        default_factory=VolcanoReviewPolicy
    )


class DiannWorkflowConfig(WorkflowBaseConfig):
    """Config for DIA-NN-to-biology workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.DIANN
    result_tsv_path: Path
    design_tsv_path: Path
    proteins_fasta_path: Path
    protocol_context_tsv_path: Path | None = None
    config_path: Path | None = None
    annotation_tsv_path: Path | None = None
    context_annotation_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    include_decoys: bool = False
    max_q_value: float = Field(default=0.01, ge=0.0, le=1.0)
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy = Field(
        default_factory=VolcanoReviewPolicy
    )


class MaxquantWorkflowConfig(WorkflowBaseConfig):
    """Config for MaxQuant-to-biology workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.MAXQUANT
    evidence_txt_path: Path
    peptides_txt_path: Path
    protein_groups_txt_path: Path
    design_tsv_path: Path
    proteins_fasta_path: Path
    protocol_context_tsv_path: Path | None = None
    config_path: Path | None = None
    annotation_tsv_path: Path | None = None
    context_annotation_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    include_only_identified_by_site: bool = False
    allow_empty_lfq_signal: bool = False
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy = Field(
        default_factory=VolcanoReviewPolicy
    )


class TmtWorkflowConfig(WorkflowBaseConfig):
    """Config for TMT report-workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.TMT
    result_tsv_path: Path
    design_tsv_path: Path
    control_channel: str = Field(..., min_length=1)
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.MAXQUANT
    mapping: TmtReporterColumnMapping = Field(
        default_factory=TmtReporterColumnMapping
    )
    channel_columns: tuple[TmtReporterChannelColumn, ...] = Field(default_factory=tuple)
    channel_normalization_method: TmtNormalizationMethod = TmtNormalizationMethod.MEDIAN
    differential_normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    batch_field: str = "batch"
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)
    pairing_field: str | None = None


class SilacWorkflowConfig(WorkflowBaseConfig):
    """Config for SILAC report-workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.SILAC
    input_tsv_path: Path
    design_tsv_path: Path
    mapping: SilacColumnMapping = Field(default_factory=SilacColumnMapping)
    quantification_policy: SilacQuantificationPolicy = Field(
        default_factory=SilacQuantificationPolicy
    )
    differential_normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    batch_field: str = "batch"
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)
    pairing_field: str | None = None


class PtmWorkflowConfig(WorkflowBaseConfig):
    """Config for PTM site-workflow dispatch."""

    mode: WorkflowMode = WorkflowMode.PTM
    evidence_tsv_path: Path
    proteins_fasta_path: Path
    feature_tsv_path: Path
    design_tsv_path: Path
    mapping: PtmLocalizationColumnMapping = Field(
        default_factory=lambda: PtmLocalizationColumnMapping(
            sample_id="sample_id",
            spectrum_id="spectrum_id",
            peptide="peptide",
            charge="charge",
            score="score",
            protein_refs="proteins",
            q_value="q_value",
            localization_score="localization_score",
            localization_probability="localization_probability",
            candidate_sites="candidate_sites",
            decoy_label="decoy_label",
            protein_separator=";",
            site_separator=";",
        )
    )
    fragment_support_json_path: Path | None = None
    ambiguity_policy: PtmSiteQuantAmbiguityPolicy = PtmSiteQuantAmbiguityPolicy.PRESERVE
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    batch_field: str = "batch"
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)
    pairing_field: str | None = None
    protein_correction_mode: PtmProteinCorrectionMode = PtmProteinCorrectionMode.NONE
    motif_flank_size: int = Field(default=7, ge=1)
    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    direction: PtmMotifRegulationDirection = PtmMotifRegulationDirection.BOTH
    include_ambiguous_regulated_sites: bool = False
    include_ambiguous_background_sites: bool = False
    min_frequency_difference: float = Field(default=0.1, ge=0.0)
    min_enrichment_ratio: float = Field(default=1.5, ge=0.0)
    max_reported_term_count: int = Field(default=25, ge=1)
    annotation_tsv_path: Path | None = None
    annotation_target_species: str | None = None
    card_max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)


class TargetedWorkflowConfig(WorkflowBaseConfig):
    """Config for targeted review dispatch."""

    mode: WorkflowMode = WorkflowMode.TARGETED
    input_tsv_path: Path
    source_kind: TargetedResultSourceKind
    stage: TargetedWorkflowStage = TargetedWorkflowStage.MATRIX
    design_tsv_path: Path | None = None
    discovery_claims: tuple[TargetedValidationDiscoveryClaimInput, ...] = Field(
        default_factory=tuple
    )
    panel_assays: tuple[TargetedValidationPanelAssayInput, ...] = Field(
        default_factory=tuple
    )
    case_condition: str | None = None
    control_condition: str | None = None
    minimum_reliable_replicates_per_condition: int = Field(default=2, ge=1)
    minimum_absolute_validation_log2_effect: float = Field(default=0.4, ge=0.0)
    flat_validation_log2_threshold: float = Field(default=0.2, ge=0.0)


WorkflowConfig = (
    LabelFreeWorkflowConfig
    | DdaWorkflowConfig
    | DiannWorkflowConfig
    | MaxquantWorkflowConfig
    | TmtWorkflowConfig
    | SilacWorkflowConfig
    | PtmWorkflowConfig
    | TargetedWorkflowConfig
)

WorkflowReport: TypeAlias = (
    BiologicalResultReportBundle
    | DdaBiologicalWorkflowBundle
    | DiannBiologicalWorkflowBundle
    | MaxquantBiologicalWorkflowBundle
    | TmtExperimentWorkflowBundle
    | LabelBasedReportBundle
    | PtmSiteWorkflowBundle
    | TargetedMatrixReport
    | TargetedAssayQcReport
    | TargetedValidationWorkflowReport
)

WorkflowSourceReport: TypeAlias = TargetedResultImportReport

WorkflowExportManifest: TypeAlias = (
    BiologicalResultReportExportManifest
    | DdaBiologicalWorkflowExportManifest
    | DiannBiologicalWorkflowExportManifest
    | MaxquantBiologicalWorkflowExportManifest
    | TmtExperimentWorkflowExportManifest
    | LabelBasedReportExportManifest
    | PtmSiteWorkflowExportManifest
    | TargetedMatrixWorkflowExportManifest
    | TargetedAssayQcWorkflowExportManifest
    | AdvancedTargetedWorkflowManifest
)


class WorkflowResult(StandardWorkflowResult):
    """Stable result packet returned by the core workflow orchestrator."""

    model_config = ConfigDict(extra="forbid")

    mode: WorkflowMode
    report: WorkflowReport
    source_report: WorkflowSourceReport | None = None
    manifest: WorkflowExportManifest | None = None
    design_row_count: int | None = Field(default=None, ge=0)
    outputs: dict[str, str] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)

    @property
    def export_manifest(self) -> WorkflowExportManifest | None:
        """Backward-compatible alias for the standardized manifest field."""

        return self.manifest


def run_proteomics_workflow(config: WorkflowConfig) -> WorkflowResult:
    """Run one supported proteomics workflow through the owned core API."""

    if isinstance(config, LabelFreeWorkflowConfig):
        return _run_label_free_workflow(config)
    if isinstance(config, DdaWorkflowConfig):
        return _run_dda_workflow(config)
    if isinstance(config, DiannWorkflowConfig):
        return _run_diann_workflow(config)
    if isinstance(config, MaxquantWorkflowConfig):
        return _run_maxquant_workflow(config)
    if isinstance(config, TmtWorkflowConfig):
        return _run_tmt_workflow(config)
    if isinstance(config, SilacWorkflowConfig):
        return _run_silac_workflow(config)
    if isinstance(config, PtmWorkflowConfig):
        return _run_ptm_workflow(config)
    if isinstance(config, TargetedWorkflowConfig):
        return _run_targeted_workflow(config)
    raise TypeError(f"unsupported workflow config type: {type(config)!r}")


def _run_label_free_workflow(config: LabelFreeWorkflowConfig) -> WorkflowResult:
    experiment_design = _load_design(config.design_tsv_path)
    report = build_biological_result_report_bundle(
        config.input_tsv_path,
        experiment_design,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        annotation_tsv_path=config.annotation_tsv_path,
        context_annotation_tsv_path=config.context_annotation_tsv_path,
        go_annotation_tsv_path=config.go_annotation_tsv_path,
        pathway_membership_tsv_path=config.pathway_membership_tsv_path,
        complex_membership_tsv_path=config.complex_membership_tsv_path,
        mapping=config.mapping,
        aggregation_method=config.aggregation_method,
        top_n=config.top_n,
        chunk_size_rows=config.chunk_size_rows,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        selection_policy=config.selection_policy,
        volcano_policy=config.volcano_policy,
    )
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_biological_result_report_bundle(report, config.output_dir)
        manifest_path = config.output_dir / "biological_report_manifest.json"
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "manifest_json": str(manifest_path),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(experiment_design.entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed label-free matrix, differential, annotation, enrichment, and reporting through the shared biological workflow owner"
        ),
    )


def _run_dda_workflow(config: DdaWorkflowConfig) -> WorkflowResult:
    experiment_design = _load_design(config.design_tsv_path)
    adapter_kind = (
        SearchAdapterKind.MSFRAGGER
        if config.mode is WorkflowMode.FRAGPIPE
        else config.adapter_kind
    )
    dialect_id = "fragpipe-psm" if config.mode is WorkflowMode.FRAGPIPE else config.dialect_id
    report = build_dda_biological_workflow_bundle(
        config.search_result_tsv_path,
        experiment_design,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        adapter_kind=adapter_kind,
        generic_mapping_path=config.generic_mapping_path,
        dialect_id=dialect_id,
        acceptance_policy=DdaPsmAcceptancePolicy(max_q_value=config.psm_q_value_threshold),
        parsimony_variant=config.parsimony_variant,
        aggregation_method=config.aggregation_method,
        top_n=config.top_n,
        chunk_size_rows=config.chunk_size_rows,
        minimum_shared_peptides=config.minimum_shared_peptides,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        source_protein_tsv_path=config.source_protein_tsv_path,
        annotation_tsv_path=config.annotation_tsv_path,
        go_annotation_tsv_path=config.go_annotation_tsv_path,
        pathway_membership_tsv_path=config.pathway_membership_tsv_path,
        complex_membership_tsv_path=config.complex_membership_tsv_path,
        selection_policy=config.selection_policy,
        volcano_policy=config.volcano_policy,
    )
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_dda_biological_workflow_bundle(report, config.output_dir)
        manifest_name = (
            "fragpipe_biological_report_manifest.json"
            if config.mode is WorkflowMode.FRAGPIPE
            else "dda_biological_report_manifest.json"
        )
        manifest_path = config.output_dir / manifest_name
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "manifest_json": str(manifest_path),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(experiment_design.entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed DDA, generic PSM, or FragPipe input through the governed DDA biological workflow owner"
        ),
    )


def _run_diann_workflow(config: DiannWorkflowConfig) -> WorkflowResult:
    experiment_design = _load_design(config.design_tsv_path)
    report = build_diann_biological_workflow_bundle(
        config.result_tsv_path,
        experiment_design,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        config_path=config.config_path,
        annotation_tsv_path=config.annotation_tsv_path,
        context_annotation_tsv_path=config.context_annotation_tsv_path,
        include_decoys=config.include_decoys,
        max_q_value=config.max_q_value,
        peptide_rollup_method=config.peptide_rollup_method,
        target_kind=config.target_kind,
        shared_peptide_policy=config.shared_peptide_policy,
        protein_rollup_method=config.protein_rollup_method,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        go_annotation_tsv_path=config.go_annotation_tsv_path,
        pathway_membership_tsv_path=config.pathway_membership_tsv_path,
        complex_membership_tsv_path=config.complex_membership_tsv_path,
        selection_policy=config.selection_policy,
        volcano_policy=config.volcano_policy,
    )
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_diann_biological_workflow_bundle(report, config.output_dir)
        manifest_path = config.output_dir / "diann_biological_report_manifest.json"
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "manifest_json": str(manifest_path),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(experiment_design.entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed DIA-NN input through the governed DIA import, matrix, QC, differential, and biology workflow owner"
        ),
    )


def _run_maxquant_workflow(config: MaxquantWorkflowConfig) -> WorkflowResult:
    experiment_design = _load_design(config.design_tsv_path)
    report = build_maxquant_biological_workflow_bundle(
        config.evidence_txt_path,
        experiment_design,
        peptides_txt_path=config.peptides_txt_path,
        protein_groups_txt_path=config.protein_groups_txt_path,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        config_path=config.config_path,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        annotation_tsv_path=config.annotation_tsv_path,
        context_annotation_tsv_path=config.context_annotation_tsv_path,
        go_annotation_tsv_path=config.go_annotation_tsv_path,
        pathway_membership_tsv_path=config.pathway_membership_tsv_path,
        complex_membership_tsv_path=config.complex_membership_tsv_path,
        selection_policy=config.selection_policy,
        volcano_policy=config.volcano_policy,
        acceptance_policy=MaxquantProteinGroupAcceptancePolicy(
            exclude_only_identified_by_site=not config.include_only_identified_by_site,
            require_lfq_signal=not config.allow_empty_lfq_signal,
        ),
    )
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_maxquant_biological_workflow_bundle(report, config.output_dir)
        manifest_path = config.output_dir / "maxquant_biological_report_manifest.json"
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "manifest_json": str(manifest_path),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(experiment_design.entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed MaxQuant evidence through the governed protein-group acceptance and biology workflow owner"
        ),
    )


def _run_tmt_workflow(config: TmtWorkflowConfig) -> WorkflowResult:
    report = build_tmt_experiment_workflow_bundle(
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
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_tmt_experiment_workflow_bundle(report, config.output_dir)
        manifest_path = config.output_dir / "tmt_workflow_manifest.json"
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "workflow_manifest_json": str(manifest_path),
            "report_manifest_json": str(
                config.output_dir / manifest.artifacts.label_based_report_manifest_json
            ),
            "manifest_json": str(
                config.output_dir / manifest.artifacts.label_based_report_manifest_json
            ),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(report.design_report.accepted_entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed TMT reporter evidence through the governed TMT experiment workflow owner"
        ),
    )


def _run_silac_workflow(config: SilacWorkflowConfig) -> WorkflowResult:
    experiment_design = _load_design(config.design_tsv_path)
    report = build_silac_label_based_report_bundle(
        config.input_tsv_path,
        experiment_design,
        mapping=config.mapping,
        quantification_policy=config.quantification_policy,
        differential_normalization_method=config.differential_normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        batch_field=config.batch_field,
        covariate_fields=tuple(dict.fromkeys(config.covariate_fields)),
        pairing_field=config.pairing_field,
    )
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_label_based_report_bundle(report, config.output_dir)
        manifest_path = config.output_dir / "label_based_report_manifest.json"
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "manifest_json": str(manifest_path),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(experiment_design.entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed SILAC evidence through the governed SILAC label-based workflow owner"
        ),
    )


def _run_ptm_workflow(config: PtmWorkflowConfig) -> WorkflowResult:
    report = build_ptm_site_workflow_bundle(
        config.evidence_tsv_path,
        config.proteins_fasta_path,
        feature_tsv_path=config.feature_tsv_path,
        design_path=config.design_tsv_path,
        mapping=config.mapping,
        fragment_support_json_path=config.fragment_support_json_path,
        ambiguity_policy=config.ambiguity_policy,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        protein_correction_mode=config.protein_correction_mode,
        batch_field=config.batch_field,
        covariate_fields=tuple(dict.fromkeys(config.covariate_fields)),
        pairing_field=config.pairing_field,
        motif_flank_size=config.motif_flank_size,
        motif_selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=config.max_adjusted_p_value,
            min_absolute_log2_fold_change=config.min_absolute_log2_fold_change,
            direction=config.direction,
            include_ambiguous_regulated_sites=config.include_ambiguous_regulated_sites,
            include_ambiguous_background_sites=config.include_ambiguous_background_sites,
        ),
        motif_comparison_policy=PtmMotifComparisonPolicy(
            min_frequency_difference=config.min_frequency_difference,
            min_enrichment_ratio=config.min_enrichment_ratio,
            max_reported_term_count=config.max_reported_term_count,
        ),
        annotation_tsv_path=config.annotation_tsv_path,
        annotation_target_species=config.annotation_target_species,
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=config.max_adjusted_p_value,
            min_absolute_log2_fold_change=config.min_absolute_log2_fold_change,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(
            max_adjusted_p_value=config.card_max_adjusted_p_value
        ),
    )
    manifest = None
    outputs: dict[str, str] = {}
    if config.output_dir is not None:
        manifest = write_ptm_site_workflow_bundle(report, config.output_dir)
        manifest_path = config.output_dir / "ptm_site_workflow_manifest.json"
        atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
        outputs = {
            "output_dir": str(config.output_dir),
            "workflow_manifest_json": str(manifest_path),
            "report_manifest_json": str(
                config.output_dir / manifest.artifacts.ptm_report_manifest_json
            ),
            "manifest_json": str(
                config.output_dir / manifest.artifacts.ptm_report_manifest_json
            ),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        manifest=manifest,
        design_row_count=len(report.experiment_design.entries),
        artifacts=_workflow_artifact_map(outputs, manifest),
        warnings=_workflow_warnings(report=report),
        rejected_evidence=_workflow_rejected_evidence(report=report),
        outputs=outputs,
        note=(
            "workflow orchestrator routed localized PTM evidence through the governed PTM site workflow owner"
        ),
    )


def _run_targeted_workflow(config: TargetedWorkflowConfig) -> WorkflowResult:
    import_report = _build_targeted_import_report(
        config.input_tsv_path,
        source_kind=config.source_kind,
    )
    if config.stage is TargetedWorkflowStage.MATRIX:
        report = build_targeted_matrix_report(import_report)
        matrix_manifest: TargetedMatrixWorkflowExportManifest | None = None
        matrix_outputs: dict[str, str] = {}
        if config.output_dir is not None:
            matrix_manifest = export_targeted_matrix_workflow_artifacts(
                import_report,
                report,
                config.output_dir,
            )
            manifest_path = config.output_dir / "targeted_matrix_workflow_manifest.json"
            atomic_write_text(manifest_path, matrix_manifest.to_stable_json() + "\n")
            matrix_outputs = {
                "output_dir": str(config.output_dir),
                "workflow_manifest_json": str(manifest_path),
                "manifest_json": str(manifest_path),
            }
        note = (
            "workflow orchestrator routed targeted observations through the governed target-matrix owner"
        )
        return WorkflowResult(
            mode=config.mode,
            report=report,
            source_report=import_report,
            manifest=matrix_manifest,
            artifacts=_workflow_artifact_map(matrix_outputs, matrix_manifest),
            warnings=_workflow_warnings(source_report=import_report, report=report),
            rejected_evidence=_workflow_rejected_evidence(
                source_report=import_report,
                report=report,
            ),
            outputs=matrix_outputs,
            note=note,
        )
    if config.stage is TargetedWorkflowStage.VALIDATION:
        if config.output_dir is None:
            raise ValueError("targeted validation workflow requires an output directory")
        if config.design_tsv_path is None:
            raise ValueError("targeted validation workflow requires a design table")
        if config.case_condition is None or config.control_condition is None:
            raise ValueError(
                "targeted validation workflow requires case and control conditions"
            )
        experiment_design = _load_design(config.design_tsv_path)
        report = run_targeted_validation_workflow(
            TargetedValidationWorkflowConfig(
                result_tsv_path=config.input_tsv_path,
                design_tsv_path=config.design_tsv_path,
                output_dir=config.output_dir,
                discovery_claims=config.discovery_claims,
                panel_assays=config.panel_assays,
                source_kind=config.source_kind,
                case_condition=config.case_condition,
                control_condition=config.control_condition,
                minimum_reliable_replicates_per_condition=(
                    config.minimum_reliable_replicates_per_condition
                ),
                minimum_absolute_validation_log2_effect=(
                    config.minimum_absolute_validation_log2_effect
                ),
                flat_validation_log2_threshold=config.flat_validation_log2_threshold,
            )
        )
        validation_outputs: dict[str, str] = {}
        if config.output_dir is not None:
            manifest_path = config.output_dir / "advanced_targeted_workflow_manifest.json"
            validation_outputs = {
                "output_dir": str(config.output_dir),
                "workflow_manifest_json": str(manifest_path),
                "manifest_json": str(manifest_path),
            }
        return WorkflowResult(
            mode=config.mode,
            report=report,
            source_report=report.import_report,
            manifest=report.manifest,
            design_row_count=len(experiment_design.entries),
            artifacts=_workflow_artifact_map(
                validation_outputs,
                report.manifest,
                report=report,
            ),
            warnings=_workflow_warnings(
                source_report=report.import_report,
                report=report,
            ),
            rejected_evidence=_workflow_rejected_evidence(
                source_report=report.import_report,
                report=report,
            ),
            outputs=validation_outputs,
            note=(
                "workflow orchestrator routed targeted observations through the governed targeted validation owner"
            ),
        )
    design_entries: tuple[ExperimentalDesignEntry, ...] = ()
    design_row_count = None
    if config.design_tsv_path is not None:
        experiment_design = _load_design(config.design_tsv_path)
        design_entries = experiment_design.entries
        design_row_count = len(experiment_design.entries)
    report = build_targeted_assay_qc_report(
        import_report,
        design_entries,
    )
    assay_qc_manifest: TargetedAssayQcWorkflowExportManifest | None = None
    assay_qc_outputs: dict[str, str] = {}
    if config.output_dir is not None:
        matrix_report = build_targeted_matrix_report(import_report)
        assay_qc_manifest = export_targeted_assay_qc_workflow_artifacts(
            import_report,
            matrix_report,
            report,
            config.output_dir,
        )
        manifest_path = config.output_dir / "targeted_assay_qc_workflow_manifest.json"
        atomic_write_text(manifest_path, assay_qc_manifest.to_stable_json() + "\n")
        assay_qc_outputs = {
            "output_dir": str(config.output_dir),
            "workflow_manifest_json": str(manifest_path),
            "manifest_json": str(manifest_path),
        }
    return WorkflowResult(
        mode=config.mode,
        report=report,
        source_report=import_report,
        manifest=assay_qc_manifest,
        design_row_count=design_row_count,
        artifacts=_workflow_artifact_map(assay_qc_outputs, assay_qc_manifest),
        warnings=_workflow_warnings(source_report=import_report, report=report),
        rejected_evidence=_workflow_rejected_evidence(
            source_report=import_report,
            report=report,
        ),
        outputs=assay_qc_outputs,
        note=(
            "workflow orchestrator routed targeted observations through the governed targeted assay-qc owner"
        ),
    )


def _load_design(path: Path) -> ExperimentDesign:
    report = parse_experimental_design_table(path)
    if report.rejected_rows:
        raise ValueError("design table contains rejected rows")
    return build_experiment_design(report.accepted_entries)


def _build_targeted_import_report(
    input_tsv_path: Path,
    *,
    source_kind: TargetedResultSourceKind,
) -> TargetedResultImportReport:
    if source_kind is TargetedResultSourceKind.SKYLINE_EXPORT:
        return build_skyline_result_import_report(input_tsv_path)
    return build_transition_table_result_import_report(input_tsv_path)


def _workflow_artifact_map(
    outputs: dict[str, str],
    manifest: WorkflowExportManifest | None,
    *,
    report: object | None = None,
) -> dict[str, str]:
    artifacts = dict(outputs)
    if manifest is not None and hasattr(manifest, "artifacts"):
        artifacts.update(artifact_name_map(getattr(manifest, "artifacts")))
    if report is not None and hasattr(report, "artifacts"):
        artifacts.update(dict(getattr(report, "artifacts")))
    return artifacts


def _workflow_warnings(
    *,
    source_report: WorkflowSourceReport | None = None,
    report: object | None = None,
) -> tuple[ResultWarningEntry, ...]:
    warnings: list[ResultWarningEntry] = []
    if report is not None and hasattr(report, "warnings"):
        warnings.extend(getattr(report, "warnings"))
    source_rejected_rows: tuple[object, ...] = ()
    if source_report is not None and hasattr(source_report, "rejected_rows"):
        source_rejected_rows = cast(
            tuple[object, ...],
            getattr(source_report, "rejected_rows"),
        )
    if source_rejected_rows:
        warnings.append(
            build_result_warning(
                warning_id="workflow:source-rejections",
                warning_code="source_rejected_rows_present",
                source_surface="workflow_orchestrator",
                message=(
                    f"{len(source_rejected_rows)} source evidence rows were rejected "
                    "before downstream workflow analysis"
                ),
            )
        )
    return tuple(warnings)


def _workflow_rejected_evidence(
    *,
    source_report: WorkflowSourceReport | None = None,
    report: object | None = None,
) -> tuple[RejectedEvidenceEntry, ...]:
    if report is not None and hasattr(report, "rejected_evidence"):
        return tuple(getattr(report, "rejected_evidence"))
    source_rejected_rows: tuple[object, ...] = ()
    if source_report is not None and hasattr(source_report, "rejected_rows"):
        source_rejected_rows = cast(
            tuple[object, ...],
            getattr(source_report, "rejected_rows"),
        )
    if source_rejected_rows:
        return build_rejected_evidence_entries_from_issue_rows(
            source_rejected_rows,
            source_surface="workflow_orchestrator",
        )
    return ()


__all__ = [
    "DdaWorkflowConfig",
    "DiannWorkflowConfig",
    "LabelFreeWorkflowConfig",
    "MaxquantWorkflowConfig",
    "PtmWorkflowConfig",
    "SilacWorkflowConfig",
    "TargetedWorkflowConfig",
    "TargetedWorkflowStage",
    "TmtWorkflowConfig",
    "WorkflowConfig",
    "WorkflowExportManifest",
    "WorkflowMode",
    "WorkflowReport",
    "WorkflowResult",
    "WorkflowSourceReport",
    "run_proteomics_workflow",
]
