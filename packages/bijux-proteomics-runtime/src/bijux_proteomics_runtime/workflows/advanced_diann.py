# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Resumable runtime integration for the advanced DIA-NN workflow."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.diann_import import (
    DiaNnBundleImportReport,
    build_diann_import_report,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import (
    build_experiment_design_validity_report,
    build_experiment_feasibility_report,
)
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannWorkflowConfig,
    AdvancedDiannWorkflowReport,
    build_advanced_diann_workflow_report_from_bundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
    DiannQuantMatrixBundle,
    build_diann_biological_workflow_bundle_from_reports,
    build_diann_quant_matrix_bundle,
)
from bijux_proteomics_foundation import JsonModel, hash_payload
from bijux_proteomics_runtime.artifacts import build_step_artifact
from bijux_proteomics_runtime.resume import (
    WorkflowResumeConfig,
    WorkflowResumeDisposition,
    WorkflowResumeStepState,
    build_workflow_resume_state,
    load_workflow_resume_state,
    resume_workflow,
    write_workflow_resume_state,
)
from bijux_proteomics_runtime.support.workspace import write_text_atomic
from bijux_proteomics_runtime.support.primitives.failures import FailureType
from bijux_proteomics_runtime.workflows.failure_reports import (
    WorkflowFailureReport,
    build_workflow_failure_report,
    write_workflow_failure_report,
)


class AdvancedDiannRuntimeStage(StrEnum):
    """Stable runtime stages for resumable advanced DIA-NN execution."""

    IMPORT = "advanced-diann-import"
    MATRICES = "advanced-diann-matrices"
    BIOLOGY = "advanced-diann-biology"
    REVIEW = "advanced-diann-review"


class AdvancedDiannRuntimeStatus(StrEnum):
    """Execution outcome for a resumable advanced DIA-NN runtime run."""

    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    FAILED = "failed"


class AdvancedDiannRuntimeStageDecision(JsonModel):
    """Runtime decision for one advanced DIA-NN stage during resume."""

    model_config = ConfigDict(extra="forbid")

    stage: AdvancedDiannRuntimeStage
    disposition: WorkflowResumeDisposition
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class AdvancedDiannRuntimeRunReport(JsonModel):
    """Reviewable report over resumable advanced DIA-NN runtime execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: AdvancedDiannRuntimeStatus
    completed_stage_ids: tuple[str, ...] = Field(default_factory=tuple)
    reused_stage_ids: tuple[str, ...] = Field(default_factory=tuple)
    rerun_stage_ids: tuple[str, ...] = Field(default_factory=tuple)
    resume_state_path: str = Field(..., min_length=1)
    failure_report_path: str | None = None
    decisions: tuple[AdvancedDiannRuntimeStageDecision, ...] = Field(default_factory=tuple)
    advanced_report: AdvancedDiannWorkflowReport | None = None
    failure_report: WorkflowFailureReport | None = None
    note: str = Field(..., min_length=1)


class AdvancedDiannDryRunStatus(StrEnum):
    """Validation outcome for advanced DIA-NN workflow dry-run planning."""

    READY = "ready"
    INVALID = "invalid"


class AdvancedDiannDryRunIssue(JsonModel):
    """One blocking or advisory dry-run issue for advanced DIA-NN planning."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    input_name: str | None = None
    path: str | None = None
    condition_ids: tuple[str, ...] = Field(default_factory=tuple)


class AdvancedDiannDryRunInputCheck(JsonModel):
    """Presence and role check for one advanced DIA-NN dry-run input."""

    model_config = ConfigDict(extra="forbid")

    input_name: str = Field(..., min_length=1)
    path: str | None = None
    required: bool
    exists: bool
    note: str = Field(..., min_length=1)


class AdvancedDiannDryRunStagePlan(JsonModel):
    """One expected runtime stage in advanced DIA-NN dry-run planning."""

    model_config = ConfigDict(extra="forbid")

    stage: AdvancedDiannRuntimeStage
    description: str = Field(..., min_length=1)
    checkpoint_path: str = Field(..., min_length=1)
    schema_name: str = Field(..., min_length=1)


class AdvancedDiannDryRunOutputPlan(JsonModel):
    """One planned durable output path for advanced DIA-NN dry-run planning."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(..., min_length=1)
    stage: AdvancedDiannRuntimeStage
    required: bool
    note: str = Field(..., min_length=1)


class AdvancedDiannDryRunReport(JsonModel):
    """Algorithm-free advanced DIA-NN workflow validation and planning report."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: AdvancedDiannDryRunStatus
    output_dir: str = Field(..., min_length=1)
    input_checks: tuple[AdvancedDiannDryRunInputCheck, ...] = Field(default_factory=tuple)
    issues: tuple[AdvancedDiannDryRunIssue, ...] = Field(default_factory=tuple)
    stage_plan: tuple[AdvancedDiannDryRunStagePlan, ...] = Field(default_factory=tuple)
    output_plan: tuple[AdvancedDiannDryRunOutputPlan, ...] = Field(default_factory=tuple)
    supported_contrasts: tuple[str, ...] = Field(default_factory=tuple)
    invalid_contrasts: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_STAGE_ORDER = (
    AdvancedDiannRuntimeStage.IMPORT,
    AdvancedDiannRuntimeStage.MATRICES,
    AdvancedDiannRuntimeStage.BIOLOGY,
    AdvancedDiannRuntimeStage.REVIEW,
)

_PLANNED_REVIEW_OUTPUTS = (
    ("diann_biological_report_manifest.json", AdvancedDiannRuntimeStage.REVIEW, True, "governed base biological workflow manifest"),
    ("advanced_diann_graph_final_results.tsv", AdvancedDiannRuntimeStage.REVIEW, True, "graph-backed final result review table"),
    ("advanced_diann_accepted_proteins.tsv", AdvancedDiannRuntimeStage.REVIEW, True, "accepted protein decision table"),
    ("advanced_diann_downgraded_proteins.tsv", AdvancedDiannRuntimeStage.REVIEW, True, "downgraded protein decision table"),
    ("advanced_diann_belief_audit_summary.tsv", AdvancedDiannRuntimeStage.REVIEW, True, "belief audit summary table"),
    ("advanced_diann_belief_audit.tsv", AdvancedDiannRuntimeStage.REVIEW, True, "belief audit detail table"),
    ("advanced_diann_summary.tsv", AdvancedDiannRuntimeStage.REVIEW, True, "advanced dia-nn workflow summary table"),
    ("advanced_diann_workflow_manifest.json", AdvancedDiannRuntimeStage.REVIEW, True, "advanced dia-nn top-level workflow manifest"),
)
_PLANNED_FRAGMENT_OUTPUTS = (
    ("advanced_diann_fragment_coelution_runs.tsv", AdvancedDiannRuntimeStage.REVIEW, False, "optional fragment coelution run summary"),
    ("advanced_diann_fragment_coelution_fragments.tsv", AdvancedDiannRuntimeStage.REVIEW, False, "optional fragment coelution fragment evidence"),
)


def dry_run_resumable_advanced_diann_workflow(
    config: AdvancedDiannWorkflowConfig,
) -> AdvancedDiannDryRunReport:
    """Validate advanced DIA-NN inputs and plan runtime stages without running algorithms."""

    workflow_id = _advanced_diann_runtime_workflow_id(config)
    input_checks = _build_dry_run_input_checks(config)
    issues = _build_dry_run_issues(config, input_checks=input_checks)
    issue_codes = {issue.code for issue in issues}
    return AdvancedDiannDryRunReport(
        workflow_id=workflow_id,
        status=(
            AdvancedDiannDryRunStatus.READY
            if not issues
            else AdvancedDiannDryRunStatus.INVALID
        ),
        output_dir=str(config.output_dir),
        input_checks=input_checks,
        issues=issues,
        stage_plan=_build_dry_run_stage_plan(config),
        output_plan=_build_dry_run_output_plan(config),
        supported_contrasts=_dry_run_supported_contrasts(config, issue_codes=issue_codes),
        invalid_contrasts=_dry_run_invalid_contrasts(config, issue_codes=issue_codes),
        note=(
            "advanced dia-nn dry run validates input presence, design and contrast "
            "feasibility, expected runtime stages, and planned durable outputs "
            "without running import, matrix, biology, or review algorithms"
        ),
    )


def run_resumable_advanced_diann_workflow(
    config: AdvancedDiannWorkflowConfig,
    *,
    through_stage: AdvancedDiannRuntimeStage | None = None,
) -> AdvancedDiannRuntimeRunReport:
    """Run advanced DIA-NN through a resumable runtime stage boundary."""

    config.output_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = config.output_dir / "checkpoints" / "advanced_diann_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    workflow_id = _advanced_diann_runtime_workflow_id(config)
    try:
        design_entries = _load_valid_design_entries(config)
    except _AdvancedDiannExpectedFailure as exc:
        failure_report, failure_report_path = _write_advanced_diann_failure_report(
            config=config,
            workflow_id=workflow_id,
            stage_id="advanced-diann-input-validation",
            failure_type=FailureType.INPUT_INVALID,
            message=exc.message,
            reason_codes=exc.reason_codes,
        )
        return AdvancedDiannRuntimeRunReport(
            workflow_id=workflow_id,
            status=AdvancedDiannRuntimeStatus.FAILED,
            completed_stage_ids=(),
            reused_stage_ids=(),
            rerun_stage_ids=(),
            resume_state_path=str(runtime_dir / "workflow_resume_state.json"),
            failure_report_path=str(failure_report_path),
            decisions=(),
            advanced_report=None,
            failure_report=failure_report,
            note=(
                "runtime wrote a structured advanced dia-nn failure report for "
                "invalid workflow input design"
            ),
        )
    failure_report_path = config.output_dir / "failure_report.json"
    if failure_report_path.exists():
        failure_report_path.unlink()

    persisted_state = (
        load_workflow_resume_state(runtime_dir)
        if (runtime_dir / "workflow_resume_state.json").exists()
        else None
    )
    reused_stage_ids: tuple[str, ...] = ()
    reused_stage_outputs: dict[AdvancedDiannRuntimeStage, JsonModel] = {}
    resume_decisions_by_stage: dict[str, tuple[WorkflowResumeDisposition, tuple[str, ...]]] = {}
    if persisted_state is not None:
        resume_report = resume_workflow(
            runtime_dir,
            WorkflowResumeConfig(
                workflow_id=workflow_id,
                input_payloads=_resume_config_payloads(config),
            ),
        )
        for decision in resume_report.decisions:
            resume_decisions_by_stage[decision.step_id] = (
                decision.disposition,
                decision.reasons,
            )
        validated_reused_stages, reused_stage_outputs = _load_reusable_stage_outputs(
            config,
            resume_decisions_by_stage=resume_decisions_by_stage,
        )
        reused_stage_ids = tuple(stage.value for stage in validated_reused_stages)

    completed_states: list[WorkflowResumeStepState] = []
    completed_stage_ids: list[str] = []
    rerun_stage_ids: list[str] = []
    decisions: list[AdvancedDiannRuntimeStageDecision] = []
    import_report: DiaNnBundleImportReport | None = None
    quant_matrix_bundle: DiannQuantMatrixBundle | None = None
    base_bundle: DiannBiologicalWorkflowBundle | None = None
    advanced_report: AdvancedDiannWorkflowReport | None = None

    for stage in _STAGE_ORDER:
        decision = resume_decisions_by_stage.get(
            stage.value,
            (WorkflowResumeDisposition.RERUN, ("stage_not_completed",)),
        )
        stage_reused = stage.value in reused_stage_ids
        if stage_reused:
            decisions.append(
                AdvancedDiannRuntimeStageDecision(
                    stage=stage,
                    disposition=WorkflowResumeDisposition.REUSED,
                    reasons=decision[1],
                )
            )
            if stage is AdvancedDiannRuntimeStage.IMPORT:
                import_report = reused_stage_outputs[stage]
            elif stage is AdvancedDiannRuntimeStage.MATRICES:
                quant_matrix_bundle = reused_stage_outputs[stage]
                import_report = quant_matrix_bundle.import_report
            elif stage is AdvancedDiannRuntimeStage.BIOLOGY:
                base_bundle = reused_stage_outputs[stage]
                import_report = base_bundle.import_report
                quant_matrix_bundle = DiannQuantMatrixBundle(
                    import_report=base_bundle.import_report,
                    precursor_matrix_report=base_bundle.precursor_matrix_report,
                    peptide_matrix_report=base_bundle.peptide_matrix_report,
                    protein_matrix_report=base_bundle.protein_matrix_report,
                    note="reconstructed runtime matrix bundle from persisted biological bundle",
                )
            else:
                advanced_report = reused_stage_outputs[stage]
                base_bundle = advanced_report.diann_workflow
                import_report = base_bundle.import_report
                quant_matrix_bundle = DiannQuantMatrixBundle(
                    import_report=base_bundle.import_report,
                    precursor_matrix_report=base_bundle.precursor_matrix_report,
                    peptide_matrix_report=base_bundle.peptide_matrix_report,
                    protein_matrix_report=base_bundle.protein_matrix_report,
                    note="reconstructed runtime matrix bundle from persisted advanced report",
                )
            completed_stage_ids.append(stage.value)
            completed_states.append(
                _persisted_step_state_for_stage(
                    stage=stage,
                    config=config,
                    completed_states=tuple(completed_states),
                    import_report=import_report,
                    quant_matrix_bundle=quant_matrix_bundle,
                    base_bundle=base_bundle,
                    advanced_report=advanced_report,
                )
            )
            continue

        rerun_stage_ids.append(stage.value)
        decisions.append(
            AdvancedDiannRuntimeStageDecision(
                stage=stage,
                disposition=WorkflowResumeDisposition.RERUN,
                reasons=decision[1],
            )
        )
        if stage is AdvancedDiannRuntimeStage.IMPORT:
            import_report = build_diann_import_report(
                config.result_tsv_path,
                config_path=config.config_path,
            )
            _write_stage_payload(
                _stage_payload_path(runtime_dir, stage),
                import_report,
            )
        elif stage is AdvancedDiannRuntimeStage.MATRICES:
            assert import_report is not None
            quant_matrix_bundle = build_diann_quant_matrix_bundle(
                import_report,
                include_decoys=config.include_decoys,
                max_q_value=config.max_q_value,
                peptide_rollup_method=config.peptide_rollup_method,
                target_kind=config.target_kind,
                shared_peptide_policy=config.shared_peptide_policy,
                protein_rollup_method=config.protein_rollup_method,
            )
            _write_stage_payload(
                _stage_payload_path(runtime_dir, stage),
                quant_matrix_bundle,
            )
        elif stage is AdvancedDiannRuntimeStage.BIOLOGY:
            assert import_report is not None
            assert quant_matrix_bundle is not None
            base_bundle = build_diann_biological_workflow_bundle_from_reports(
                import_report,
                quant_matrix_bundle,
                design_entries,
                proteins_fasta_path=config.proteins_fasta_path,
                protocol_context_tsv_path=config.protocol_context_tsv_path,
                include_decoys=config.include_decoys,
                max_q_value=config.max_q_value,
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
            )
            _write_stage_payload(
                _stage_payload_path(runtime_dir, stage),
                base_bundle,
            )
        else:
            assert base_bundle is not None
            advanced_report = build_advanced_diann_workflow_report_from_bundle(
                base_bundle,
                config,
            )
            _write_stage_payload(
                _stage_payload_path(runtime_dir, stage),
                advanced_report,
            )

        completed_stage_ids.append(stage.value)
        completed_states.append(
            _persisted_step_state_for_stage(
                stage=stage,
                config=config,
                completed_states=tuple(completed_states),
                import_report=import_report,
                quant_matrix_bundle=quant_matrix_bundle,
                base_bundle=base_bundle,
                advanced_report=advanced_report,
            )
        )
        write_workflow_resume_state(
            runtime_dir,
            build_workflow_resume_state(
                workflow_id=workflow_id,
                steps=tuple(completed_states),
            ),
        )
        if through_stage is stage:
            return AdvancedDiannRuntimeRunReport(
                workflow_id=workflow_id,
                status=AdvancedDiannRuntimeStatus.INTERRUPTED,
                completed_stage_ids=tuple(completed_stage_ids),
                reused_stage_ids=reused_stage_ids,
                rerun_stage_ids=tuple(rerun_stage_ids),
                resume_state_path=str(runtime_dir / "workflow_resume_state.json"),
                decisions=tuple(decisions),
                advanced_report=None,
                note=(
                    "runtime stopped at the requested advanced dia-nn stage boundary "
                    "after persisting resumable stage state"
                ),
            )

    assert advanced_report is not None
    return AdvancedDiannRuntimeRunReport(
        workflow_id=workflow_id,
        status=AdvancedDiannRuntimeStatus.COMPLETED,
        completed_stage_ids=tuple(completed_stage_ids),
        reused_stage_ids=reused_stage_ids,
        rerun_stage_ids=tuple(rerun_stage_ids),
        resume_state_path=str(runtime_dir / "workflow_resume_state.json"),
        failure_report_path=None,
        decisions=tuple(decisions),
        advanced_report=advanced_report,
        failure_report=None,
        note=(
            "runtime completed the advanced dia-nn workflow with resumable import, "
            "matrix, biology, and final review stages"
        ),
    )


class _AdvancedDiannExpectedFailure(Exception):
    """Internal signal for expected advanced DIA-NN workflow failures."""

    def __init__(self, *, message: str, reason_codes: tuple[str, ...]) -> None:
        super().__init__(message)
        self.message = message
        self.reason_codes = reason_codes


def _load_valid_design_entries(
    config: AdvancedDiannWorkflowConfig,
) -> tuple[object, ...]:
    report = parse_experimental_design_table(config.design_tsv_path)
    if report.rejected_rows:
        reason_codes = tuple(
            dict.fromkeys(
                issue.code
                for row in report.rejected_rows
                for issue in row.issues
            )
        )
        raise _AdvancedDiannExpectedFailure(
            message=(
                "advanced dia-nn workflow design table contains rejected rows and "
                "cannot proceed"
            ),
            reason_codes=reason_codes,
        )
    return tuple(report.accepted_entries)


def _write_advanced_diann_failure_report(
    *,
    config: AdvancedDiannWorkflowConfig,
    workflow_id: str,
    stage_id: str,
    failure_type: FailureType,
    message: str,
    reason_codes: tuple[str, ...],
) -> tuple[WorkflowFailureReport, Path]:
    report = build_workflow_failure_report(
        workflow_id=workflow_id,
        workflow_name="advanced_diann",
        stage_id=stage_id,
        failure_type=failure_type.value,
        message=message,
        reason_codes=reason_codes,
    )
    return report, write_workflow_failure_report(config.output_dir, report)


def _build_dry_run_input_checks(
    config: AdvancedDiannWorkflowConfig,
) -> tuple[AdvancedDiannDryRunInputCheck, ...]:
    checks: list[AdvancedDiannDryRunInputCheck] = []
    for input_name, path, required, note in (
        ("result_tsv_path", config.result_tsv_path, True, "required DIA-NN report table"),
        ("design_tsv_path", config.design_tsv_path, True, "required experimental design table"),
        ("proteins_fasta_path", config.proteins_fasta_path, True, "required protein FASTA database"),
        ("protocol_context_tsv_path", config.protocol_context_tsv_path, False, "optional protocol context table"),
        ("config_path", config.config_path, False, "optional DIA-NN configuration snapshot"),
        ("annotation_tsv_path", config.annotation_tsv_path, False, "optional annotation table"),
        ("context_annotation_tsv_path", config.context_annotation_tsv_path, False, "optional context annotation table"),
        ("go_annotation_tsv_path", config.go_annotation_tsv_path, False, "optional gene ontology annotation table"),
        ("pathway_membership_tsv_path", config.pathway_membership_tsv_path, False, "optional pathway membership table"),
        ("complex_membership_tsv_path", config.complex_membership_tsv_path, False, "optional complex membership table"),
        ("fragment_target_tsv_path", config.fragment_target_tsv_path, False, "optional fragment target table"),
    ):
        exists = path is not None and path.exists()
        checks.append(
            AdvancedDiannDryRunInputCheck(
                input_name=input_name,
                path=None if path is None else str(path),
                required=required,
                exists=exists,
                note=note,
            )
        )
    for index, path in enumerate(config.fragment_mzml_paths, start=1):
        checks.append(
            AdvancedDiannDryRunInputCheck(
                input_name=f"fragment_mzml_paths[{index}]",
                path=str(path),
                required=False,
                exists=path.exists(),
                note="optional mzML trace used for fragment coelution review",
            )
        )
    return tuple(checks)


def _build_dry_run_issues(
    config: AdvancedDiannWorkflowConfig,
    *,
    input_checks: tuple[AdvancedDiannDryRunInputCheck, ...],
) -> tuple[AdvancedDiannDryRunIssue, ...]:
    issues: list[AdvancedDiannDryRunIssue] = []
    issues.extend(_missing_input_file_issues(input_checks))
    issues.extend(_fragment_input_issues(config, input_checks=input_checks))
    issues.extend(_design_and_contrast_issues(config, input_checks=input_checks))
    return tuple(issues)


def _missing_input_file_issues(
    input_checks: tuple[AdvancedDiannDryRunInputCheck, ...],
) -> tuple[AdvancedDiannDryRunIssue, ...]:
    issues = []
    for check in input_checks:
        if check.required and not check.exists:
            issues.append(
                AdvancedDiannDryRunIssue(
                    code="missing_input_file",
                    message=f"required workflow input {check.input_name} is missing",
                    input_name=check.input_name,
                    path=check.path,
                )
            )
        if not check.required and check.path is not None and not check.exists:
            issues.append(
                AdvancedDiannDryRunIssue(
                    code="missing_optional_input_file",
                    message=f"optional workflow input {check.input_name} was provided but is missing",
                    input_name=check.input_name,
                    path=check.path,
                )
            )
    return tuple(issues)


def _fragment_input_issues(
    config: AdvancedDiannWorkflowConfig,
    *,
    input_checks: tuple[AdvancedDiannDryRunInputCheck, ...],
) -> tuple[AdvancedDiannDryRunIssue, ...]:
    issues: list[AdvancedDiannDryRunIssue] = []
    if config.fragment_mzml_paths and config.fragment_target_tsv_path is None:
        issues.append(
            AdvancedDiannDryRunIssue(
                code="missing_fragment_targets",
                message="fragment_target_tsv_path is required when fragment_mzml_paths are provided",
                input_name="fragment_target_tsv_path",
            )
        )
    if not config.fragment_mzml_paths and config.fragment_target_tsv_path is not None:
        issues.append(
            AdvancedDiannDryRunIssue(
                code="missing_fragment_traces",
                message="fragment_mzml_paths are required when fragment_target_tsv_path is provided",
                input_name="fragment_mzml_paths",
                path=str(config.fragment_target_tsv_path),
            )
        )
    missing_fragment_paths = tuple(
        check.path
        for check in input_checks
        if check.input_name.startswith("fragment_mzml_paths[") and not check.exists and check.path
    )
    if missing_fragment_paths:
        issues.append(
            AdvancedDiannDryRunIssue(
                code="missing_fragment_trace_file",
                message="one or more fragment mzML trace files are missing",
                input_name="fragment_mzml_paths",
                path=";".join(missing_fragment_paths),
            )
        )
    return tuple(issues)


def _design_and_contrast_issues(
    config: AdvancedDiannWorkflowConfig,
    *,
    input_checks: tuple[AdvancedDiannDryRunInputCheck, ...],
) -> tuple[AdvancedDiannDryRunIssue, ...]:
    required_inputs_present = {
        check.input_name: check.exists
        for check in input_checks
        if check.required
    }
    if not required_inputs_present.get("design_tsv_path", False):
        return ()

    design_report = parse_experimental_design_table(config.design_tsv_path)
    issues: list[AdvancedDiannDryRunIssue] = []
    for rejected_row in design_report.rejected_rows:
        for issue in rejected_row.issues:
            issues.append(
                AdvancedDiannDryRunIssue(
                    code=issue.code,
                    message=issue.message,
                    input_name="design_tsv_path",
                    path=str(config.design_tsv_path),
                )
            )
    if design_report.rejected_rows:
        return tuple(issues)

    validity_report = build_experiment_design_validity_report(
        tuple(design_report.accepted_entries),
        condition_a=config.condition_a,
        condition_b=config.condition_b,
    )
    for issue in validity_report.issues:
        issues.append(
            AdvancedDiannDryRunIssue(
                code=issue.code,
                message=issue.message,
                input_name="design_tsv_path",
                path=str(config.design_tsv_path),
                condition_ids=issue.condition_ids,
            )
        )
    return tuple(issues)


def _build_dry_run_stage_plan(
    config: AdvancedDiannWorkflowConfig,
) -> tuple[AdvancedDiannDryRunStagePlan, ...]:
    runtime_dir = config.output_dir / "checkpoints" / "advanced_diann_runtime"
    return tuple(
        AdvancedDiannDryRunStagePlan(
            stage=stage,
            description=_stage_description(stage),
            checkpoint_path=str(_stage_payload_path(runtime_dir, stage)),
            schema_name=_stage_schema_name(stage),
        )
        for stage in _STAGE_ORDER
    )


def _build_dry_run_output_plan(
    config: AdvancedDiannWorkflowConfig,
) -> tuple[AdvancedDiannDryRunOutputPlan, ...]:
    planned_outputs = [
        AdvancedDiannDryRunOutputPlan(
            relative_path="checkpoints/advanced_diann_runtime/workflow_resume_state.json",
            stage=AdvancedDiannRuntimeStage.REVIEW,
            required=True,
            note="resume state ledger persisted after each completed runtime stage",
        )
    ]
    planned_outputs.extend(
        AdvancedDiannDryRunOutputPlan(
            relative_path=f"checkpoints/advanced_diann_runtime/{stage.value}.json",
            stage=stage,
            required=True,
            note=f"persisted {stage.value} checkpoint payload for runtime reuse",
        )
        for stage in _STAGE_ORDER
    )
    planned_outputs.extend(
        AdvancedDiannDryRunOutputPlan(
            relative_path=relative_path,
            stage=stage,
            required=required,
            note=note,
        )
        for relative_path, stage, required, note in _PLANNED_REVIEW_OUTPUTS
    )
    if config.fragment_mzml_paths or config.fragment_target_tsv_path is not None:
        planned_outputs.extend(
            AdvancedDiannDryRunOutputPlan(
                relative_path=relative_path,
                stage=stage,
                required=required,
                note=note,
            )
            for relative_path, stage, required, note in _PLANNED_FRAGMENT_OUTPUTS
        )
    return tuple(planned_outputs)


def _dry_run_supported_contrasts(
    config: AdvancedDiannWorkflowConfig,
    *,
    issue_codes: set[str],
) -> tuple[str, ...]:
    if not config.design_tsv_path.exists():
        return ()
    design_report = parse_experimental_design_table(config.design_tsv_path)
    if design_report.rejected_rows:
        return ()
    if any(code.startswith("invalid_contrast_") for code in issue_codes):
        return ()
    feasibility_report = build_experiment_feasibility_report(
        tuple(design_report.accepted_entries),
        condition_a=config.condition_a,
        condition_b=config.condition_b,
    )
    return tuple(
        f"{entry.condition_a}_vs_{entry.condition_b}"
        for entry in feasibility_report.valid_contrasts
    )


def _dry_run_invalid_contrasts(
    config: AdvancedDiannWorkflowConfig,
    *,
    issue_codes: set[str],
) -> tuple[str, ...]:
    if not config.design_tsv_path.exists():
        return ()
    design_report = parse_experimental_design_table(config.design_tsv_path)
    if design_report.rejected_rows:
        return ()
    feasibility_report = build_experiment_feasibility_report(
        tuple(design_report.accepted_entries),
        condition_a=config.condition_a,
        condition_b=config.condition_b,
    )
    invalid_contrasts = [
        f"{entry.condition_a}_vs_{entry.condition_b}: {entry.message}"
        for entry in feasibility_report.invalid_contrasts
    ]
    invalid_contrast_issues = [
        issue
        for issue in feasibility_report.validity_report.issues
        if issue.code.startswith("invalid_contrast_")
    ]
    invalid_contrasts.extend(
        f"{'/'.join(issue.condition_ids) or 'requested_contrast'}: {issue.message}"
        for issue in invalid_contrast_issues
    )
    return tuple(dict.fromkeys(invalid_contrasts))


def _resume_config_payloads(config: AdvancedDiannWorkflowConfig) -> dict[str, object]:
    return {
        "annotation_tsv_sha256": _optional_file_sha256(config.annotation_tsv_path),
        "complex_membership_tsv_sha256": _optional_file_sha256(
            config.complex_membership_tsv_path
        ),
        "condition_a": config.condition_a,
        "condition_b": config.condition_b,
        "config_path_sha256": _optional_file_sha256(config.config_path),
        "context_annotation_tsv_sha256": _optional_file_sha256(
            config.context_annotation_tsv_path
        ),
        "design_tsv_sha256": _file_sha256(config.design_tsv_path),
        "fragment_apex_tolerance_seconds": config.fragment_apex_tolerance_seconds,
        "fragment_min_correlation": config.fragment_min_correlation,
        "fragment_min_passing_fragment_count": config.fragment_min_passing_fragment_count,
        "fragment_min_peak_height": config.fragment_min_peak_height,
        "fragment_mzml_sha256": tuple(
            _file_sha256(path) for path in config.fragment_mzml_paths
        ),
        "fragment_target_tsv_sha256": _optional_file_sha256(
            config.fragment_target_tsv_path
        ),
        "fragment_tolerance_da": config.fragment_tolerance_da,
        "fragment_tolerance_ppm": config.fragment_tolerance_ppm,
        "go_annotation_tsv_sha256": _optional_file_sha256(config.go_annotation_tsv_path),
        "include_decoys": config.include_decoys,
        "max_q_value": config.max_q_value,
        "normalization_method": config.normalization_method.value,
        "pathway_membership_tsv_sha256": _optional_file_sha256(
            config.pathway_membership_tsv_path
        ),
        "peptide_rollup_method": config.peptide_rollup_method.value,
        "proteins_fasta_sha256": _file_sha256(config.proteins_fasta_path),
        "protocol_context_tsv_sha256": _optional_file_sha256(
            config.protocol_context_tsv_path
        ),
        "result_tsv_sha256": _file_sha256(config.result_tsv_path),
        "selection_policy_sha256": hash_payload(
            None if config.selection_policy is None else config.selection_policy.to_dict()
        ),
        "shared_peptide_policy": config.shared_peptide_policy.value,
        "target_kind": config.target_kind.value,
        "volcano_policy_sha256": hash_payload(
            None if config.volcano_policy is None else config.volcano_policy.to_dict()
        ),
        "protein_rollup_method": config.protein_rollup_method.value,
    }


def _advanced_diann_runtime_workflow_id(config: AdvancedDiannWorkflowConfig) -> str:
    return f"advanced-diann-runtime-{hash_payload({'result': str(config.result_tsv_path), 'design': str(config.design_tsv_path), 'proteins': str(config.proteins_fasta_path), 'output_dir': str(config.output_dir)})[:16]}"


def _stage_payload_path(runtime_dir: Path, stage: AdvancedDiannRuntimeStage) -> Path:
    return runtime_dir / f"{stage.value}.json"


def _write_stage_payload(path: Path, payload: JsonModel) -> None:
    write_text_atomic(path, payload.to_stable_json() + "\n")


def _file_sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _optional_file_sha256(path: Path | None) -> str | None:
    if path is None:
        return None
    return _file_sha256(path)


def _stage_direct_input_keys(
    stage: AdvancedDiannRuntimeStage,
) -> tuple[str, ...]:
    if stage is AdvancedDiannRuntimeStage.IMPORT:
        return (
            "result_tsv_sha256",
            "config_path_sha256",
            "include_decoys",
            "max_q_value",
        )
    if stage is AdvancedDiannRuntimeStage.MATRICES:
        return (
            "include_decoys",
            "max_q_value",
            "peptide_rollup_method",
            "target_kind",
            "shared_peptide_policy",
            "protein_rollup_method",
        )
    if stage is AdvancedDiannRuntimeStage.BIOLOGY:
        return (
            "design_tsv_sha256",
            "proteins_fasta_sha256",
            "protocol_context_tsv_sha256",
            "annotation_tsv_sha256",
            "context_annotation_tsv_sha256",
            "go_annotation_tsv_sha256",
            "pathway_membership_tsv_sha256",
            "complex_membership_tsv_sha256",
            "normalization_method",
            "condition_a",
            "condition_b",
            "selection_policy_sha256",
            "volcano_policy_sha256",
            "include_decoys",
            "max_q_value",
        )
    return (
        "fragment_target_tsv_sha256",
        "fragment_mzml_sha256",
        "fragment_tolerance_da",
        "fragment_tolerance_ppm",
        "fragment_min_peak_height",
        "fragment_apex_tolerance_seconds",
        "fragment_min_correlation",
        "fragment_min_passing_fragment_count",
    )


def _persisted_step_state_for_stage(
    *,
    stage: AdvancedDiannRuntimeStage,
    config: AdvancedDiannWorkflowConfig,
    completed_states: tuple[WorkflowResumeStepState, ...],
    import_report: DiaNnBundleImportReport | None,
    quant_matrix_bundle: DiannQuantMatrixBundle | None,
    base_bundle: DiannBiologicalWorkflowBundle | None,
    advanced_report: AdvancedDiannWorkflowReport | None,
) -> WorkflowResumeStepState:
    stage_payloads: dict[AdvancedDiannRuntimeStage, JsonModel | None] = {
        AdvancedDiannRuntimeStage.IMPORT: import_report,
        AdvancedDiannRuntimeStage.MATRICES: quant_matrix_bundle,
        AdvancedDiannRuntimeStage.BIOLOGY: base_bundle,
        AdvancedDiannRuntimeStage.REVIEW: advanced_report,
    }
    payload = stage_payloads[stage]
    if payload is None:
        raise ValueError(f"missing payload for runtime stage {stage.value}")
    artifact = build_step_artifact(
        step_id=stage.value,
        description=_stage_description(stage),
        status="completed",
        input_payloads={
            f"config:{key}": value
            for key, value in _resume_config_payloads(config).items()
            if key in _stage_direct_input_keys(stage)
        }
        | {
            f"upstream:{dependency.value}": next(
                state.artifact.output_checksums
                for state in completed_states
                if state.step_id == dependency.value
            )
            for dependency in _stage_dependencies(stage)
        },
        output_payloads={"payload": payload},
        entity_counts={"rows": _stage_entity_count(stage, payload)},
        schema_names=(_stage_schema_name(stage),),
    )
    return WorkflowResumeStepState(
        step_id=stage.value,
        description=_stage_description(stage),
        depends_on=tuple(dependency.value for dependency in _stage_dependencies(stage)),
        direct_input_keys=_stage_direct_input_keys(stage),
        artifact=artifact,
    )


def _stage_dependencies(
    stage: AdvancedDiannRuntimeStage,
) -> tuple[AdvancedDiannRuntimeStage, ...]:
    if stage is AdvancedDiannRuntimeStage.IMPORT:
        return ()
    if stage is AdvancedDiannRuntimeStage.MATRICES:
        return (AdvancedDiannRuntimeStage.IMPORT,)
    if stage is AdvancedDiannRuntimeStage.BIOLOGY:
        return (AdvancedDiannRuntimeStage.IMPORT, AdvancedDiannRuntimeStage.MATRICES)
    return (AdvancedDiannRuntimeStage.BIOLOGY,)


def _stage_description(stage: AdvancedDiannRuntimeStage) -> str:
    descriptions = {
        AdvancedDiannRuntimeStage.IMPORT: "import DIA-NN precursor evidence into governed runtime review records",
        AdvancedDiannRuntimeStage.MATRICES: "build precursor, peptide, and protein DIA-NN quant matrices",
        AdvancedDiannRuntimeStage.BIOLOGY: "build QC, differential, and biological DIA-NN bundle surfaces",
        AdvancedDiannRuntimeStage.REVIEW: "write the advanced DIA-NN review directory and manifest surfaces",
    }
    return descriptions[stage]


def _stage_schema_name(stage: AdvancedDiannRuntimeStage) -> str:
    schema_names = {
        AdvancedDiannRuntimeStage.IMPORT: "diann_import_report",
        AdvancedDiannRuntimeStage.MATRICES: "diann_quant_matrix_bundle",
        AdvancedDiannRuntimeStage.BIOLOGY: "diann_biological_workflow_bundle",
        AdvancedDiannRuntimeStage.REVIEW: "advanced_diann_workflow_report",
    }
    return schema_names[stage]


def _stage_entity_count(stage: AdvancedDiannRuntimeStage, payload: JsonModel) -> int:
    if stage is AdvancedDiannRuntimeStage.IMPORT:
        report = payload
        assert isinstance(report, DiaNnBundleImportReport)
        return report.summary.accepted_precursor_count
    if stage is AdvancedDiannRuntimeStage.MATRICES:
        bundle = payload
        assert isinstance(bundle, DiannQuantMatrixBundle)
        return bundle.protein_matrix_report.summary.protein_row_count
    if stage is AdvancedDiannRuntimeStage.BIOLOGY:
        bundle = payload
        assert isinstance(bundle, DiannBiologicalWorkflowBundle)
        return bundle.summary.significant_protein_count
    report = payload
    assert isinstance(report, AdvancedDiannWorkflowReport)
    return report.summary.accepted_protein_count + report.summary.downgraded_protein_count


def _load_reusable_stage_outputs(
    config: AdvancedDiannWorkflowConfig,
    *,
    resume_decisions_by_stage: dict[str, tuple[WorkflowResumeDisposition, tuple[str, ...]]],
) -> tuple[tuple[AdvancedDiannRuntimeStage, ...], dict[AdvancedDiannRuntimeStage, JsonModel]]:
    runtime_dir = config.output_dir / "checkpoints" / "advanced_diann_runtime"
    reusable: list[AdvancedDiannRuntimeStage] = []
    outputs: dict[AdvancedDiannRuntimeStage, JsonModel] = {}
    for stage in _STAGE_ORDER:
        decision = resume_decisions_by_stage.get(stage.value)
        if decision is None or decision[0] is not WorkflowResumeDisposition.REUSED:
            break
        loader = _stage_loader(stage)
        payload_path = _stage_payload_path(runtime_dir, stage)
        if not payload_path.exists():
            break
        try:
            outputs[stage] = loader(payload_path)
        except Exception:
            break
        reusable.append(stage)
    return tuple(reusable), outputs


def _stage_loader(stage: AdvancedDiannRuntimeStage):
    if stage is AdvancedDiannRuntimeStage.IMPORT:
        return DiaNnBundleImportReport.load_json
    if stage is AdvancedDiannRuntimeStage.MATRICES:
        return DiannQuantMatrixBundle.load_json
    if stage is AdvancedDiannRuntimeStage.BIOLOGY:
        return DiannBiologicalWorkflowBundle.load_json
    return AdvancedDiannWorkflowReport.load_json


__all__ = [
    "AdvancedDiannDryRunInputCheck",
    "AdvancedDiannDryRunIssue",
    "AdvancedDiannDryRunOutputPlan",
    "AdvancedDiannDryRunReport",
    "AdvancedDiannDryRunStagePlan",
    "AdvancedDiannDryRunStatus",
    "AdvancedDiannRuntimeRunReport",
    "AdvancedDiannRuntimeStage",
    "AdvancedDiannRuntimeStageDecision",
    "AdvancedDiannRuntimeStatus",
    "dry_run_resumable_advanced_diann_workflow",
    "run_resumable_advanced_diann_workflow",
]
