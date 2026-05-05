# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_reproducibility import (
    RuntimeWorkflowBlueprintStage,
    RuntimeWorkflowBlueprintStep,
    build_runtime_workflow_blueprint,
)


def test_build_runtime_workflow_blueprint_generates_replayable_digest() -> None:
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
