# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_reproducibility import (
    PartialWorkflowRerunRequest,
    RuntimeWorkflowBlueprintStage,
    RuntimeWorkflowBlueprintStep,
    WorkflowRunSnapshot,
    WorkflowStepExecutionStatus,
    WorkflowStepRunState,
    build_runtime_workflow_blueprint,
    build_workflow_run_diff_report,
    plan_partial_workflow_rerun,
)


def test_runtime_workflow_blueprint_generates_replayable_digest() -> None:
    blueprint = build_runtime_workflow_blueprint(
        blueprint_id="wf-proteomics-main",
        study_id="study-a",
        sample_id="sample-01",
        steps=(
            RuntimeWorkflowBlueprintStep(
                step_id="intake",
                stage=RuntimeWorkflowBlueprintStage.SEQUENCE_INTAKE,
                tool_name="fasta-loader",
                input_roles=("fasta",),
                output_roles=("normalized_sequences",),
                parameter_fingerprint="a" * 16,
                schema_refs=("schema.sequence.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="search",
                stage=RuntimeWorkflowBlueprintStage.SEARCH_INGESTION,
                tool_name="comet-adapter",
                input_roles=("spectra", "search_config"),
                output_roles=("psm_table",),
                parameter_fingerprint="b" * 16,
                schema_refs=("schema.psm.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="fdr",
                stage=RuntimeWorkflowBlueprintStage.FDR,
                tool_name="fdr-engine",
                input_roles=("psm_table",),
                output_roles=("accepted_psm",),
                parameter_fingerprint="c" * 16,
                schema_refs=("schema.fdr.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="quant",
                stage=RuntimeWorkflowBlueprintStage.QUANT,
                tool_name="lfq-engine",
                input_roles=("accepted_psm",),
                output_roles=("quant_matrix",),
                parameter_fingerprint="d" * 16,
                schema_refs=("schema.quant.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="qc",
                stage=RuntimeWorkflowBlueprintStage.QC,
                tool_name="qc-engine",
                input_roles=("quant_matrix",),
                output_roles=("qc_report",),
                parameter_fingerprint="e" * 16,
                schema_refs=("schema.qc.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="evidence",
                stage=RuntimeWorkflowBlueprintStage.EVIDENCE,
                tool_name="evidence-assembler",
                input_roles=("accepted_psm", "qc_report"),
                output_roles=("evidence_graph",),
                parameter_fingerprint="f" * 16,
                schema_refs=("schema.evidence.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="intelligence",
                stage=RuntimeWorkflowBlueprintStage.INTELLIGENCE,
                tool_name="ranking-engine",
                input_roles=("evidence_graph",),
                output_roles=("review_packet",),
                parameter_fingerprint="1" * 16,
                schema_refs=("schema.review.v1",),
            ),
            RuntimeWorkflowBlueprintStep(
                step_id="lab",
                stage=RuntimeWorkflowBlueprintStage.LAB_HANDOFF,
                tool_name="lab-handoff",
                input_roles=("review_packet",),
                output_roles=("lab_plan",),
                parameter_fingerprint="2" * 16,
                schema_refs=("schema.lab.v1",),
            ),
        ),
        created_from_run_id="run-0042",
    )

    assert blueprint.workflow_digest
    assert len(blueprint.workflow_digest) == 64
    assert blueprint.steps[1].input_roles == ("search_config", "spectra")


def test_workflow_run_diff_report_captures_quant_qc_and_lab_drift() -> None:
    report = build_workflow_run_diff_report(
        WorkflowRunSnapshot(
            run_id="run-a",
            study_id="study-1",
            sample_id="sample-1",
            input_fingerprint="a" * 16,
            engine_fingerprint="b" * 16,
            parameter_fingerprint="c" * 16,
            confidence_fingerprint="d" * 16,
            quant_fingerprint="e" * 16,
            qc_fingerprint="f" * 16,
            evidence_fingerprint="1" * 16,
            lab_handoff_fingerprint="2" * 16,
        ),
        WorkflowRunSnapshot(
            run_id="run-b",
            study_id="study-1",
            sample_id="sample-1",
            input_fingerprint="a" * 16,
            engine_fingerprint="b" * 16,
            parameter_fingerprint="c" * 16,
            confidence_fingerprint="d" * 16,
            quant_fingerprint="z" * 16,
            qc_fingerprint="y" * 16,
            evidence_fingerprint="1" * 16,
            lab_handoff_fingerprint="x" * 16,
        ),
    )

    changed_fields = {entry.field_name for entry in report.entries}
    assert changed_fields == {
        "lab_handoff_fingerprint",
        "qc_fingerprint",
        "quant_fingerprint",
    }


def test_partial_workflow_rerun_expands_dependencies_and_preserves_evidence() -> None:
    plan = plan_partial_workflow_rerun(
        request=PartialWorkflowRerunRequest(
            prior_run_id="run-1",
            selected_step_ids=("search",),
        ),
        step_states=(
            WorkflowStepRunState(
                step_id="intake",
                status=WorkflowStepExecutionStatus.SUCCEEDED,
                output_artifacts=("a",),
                evidence_pointers=("ev-intake",),
            ),
            WorkflowStepRunState(
                step_id="search",
                status=WorkflowStepExecutionStatus.FAILED,
                depends_on=("intake",),
                output_artifacts=("b",),
                evidence_pointers=("ev-search",),
            ),
            WorkflowStepRunState(
                step_id="quant",
                status=WorkflowStepExecutionStatus.SKIPPED,
                depends_on=("search",),
                output_artifacts=("c",),
                evidence_pointers=("ev-quant",),
            ),
        ),
    )

    assert plan.rerun_step_ids == ("search", "quant")
    assert plan.reused_step_ids == ("intake",)
    assert plan.preserved_evidence_pointers == ("ev-intake",)
