# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.artifacts import build_step_artifact
from bijux_proteomics_runtime.resume import (
    WorkflowResumeConfig,
    WorkflowResumeDisposition,
    WorkflowResumeStepState,
    build_workflow_resume_state,
    resume_workflow,
    write_workflow_resume_state,
)


def _step(
    *,
    step_id: str,
    description: str,
    input_payloads: dict[str, object],
    output_payloads: dict[str, object],
    depends_on: tuple[str, ...] = (),
    direct_input_keys: tuple[str, ...] = (),
    status: str = "completed",
) -> WorkflowResumeStepState:
    artifact = build_step_artifact(
        step_id=step_id,
        description=description,
        status=status,
        input_payloads=input_payloads,
        output_payloads=output_payloads,
        entity_counts={"rows": 1},
        schema_names=("resume_test_row",),
    )
    return WorkflowResumeStepState(
        step_id=step_id,
        description=description,
        depends_on=depends_on,
        direct_input_keys=direct_input_keys,
        artifact=artifact,
    )


def _persist_resume_state(run_dir: Path) -> None:
    fasta_text = ">sp|P1|PROT1\nMPEPTIDER"
    parsed_records = ({"accession": "P1", "sequence": "MPEPTIDER"},)
    protein_matrix = ({"protein_id": "P1", "sample_id": "S1", "intensity": 42.0},)
    sample_metadata = (
        {"sample_id": "S1", "condition": "control"},
        {"sample_id": "S2", "condition": "treated"},
    )
    statistics_rows = ({"protein_id": "P1", "log2_fc": 1.0},)
    biology_rows = ({"pathway_id": "PWY-1", "signal": "up"},)
    parse_step = _step(
        step_id="parse-fasta",
        description="parse FASTA reference records",
        input_payloads={"config:fasta_text": fasta_text},
        output_payloads={"accepted_records": parsed_records},
        direct_input_keys=("fasta_text",),
    )
    matrix_step = _step(
        step_id="build-protein-matrix",
        description="roll up protein intensities before statistics",
        input_payloads={"upstream:parse-fasta": parse_step.artifact.output_checksums},
        output_payloads={"protein_matrix": protein_matrix},
        depends_on=("parse-fasta",),
    )
    statistics_step = _step(
        step_id="run-statistics",
        description="compare conditions using sample metadata",
        input_payloads={
            "upstream:build-protein-matrix": matrix_step.artifact.output_checksums,
            "config:sample_metadata": sample_metadata,
        },
        output_payloads={"statistics_rows": statistics_rows},
        depends_on=("build-protein-matrix",),
        direct_input_keys=("sample_metadata",),
    )
    biology_step = _step(
        step_id="build-biology",
        description="assemble pathway-level biology from protein statistics",
        input_payloads={
            "upstream:run-statistics": statistics_step.artifact.output_checksums
        },
        output_payloads={"biology_rows": biology_rows},
        depends_on=("run-statistics",),
    )
    state = build_workflow_resume_state(
        workflow_id="lfq-biology",
        steps=(parse_step, matrix_step, statistics_step, biology_step),
    )
    write_workflow_resume_state(run_dir, state)


def test_resume_workflow_reuses_completed_valid_steps_and_invalidates_downstream_metadata_steps(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "artifacts" / "resume-run"
    run_dir.mkdir(parents=True)
    _persist_resume_state(run_dir)

    report = resume_workflow(
        run_dir,
        WorkflowResumeConfig(
            workflow_id="lfq-biology",
            input_payloads={
                "fasta_text": ">sp|P1|PROT1\nMPEPTIDER",
                "sample_metadata": (
                    {"sample_id": "S1", "condition": "control"},
                    {"sample_id": "S2", "condition": "responder"},
                ),
            },
        ),
    )

    assert report.reused_step_ids == ("parse-fasta", "build-protein-matrix")
    assert report.rerun_step_ids == ("run-statistics", "build-biology")
    statistics_decision = next(
        decision
        for decision in report.decisions
        if decision.step_id == "run-statistics"
    )
    biology_decision = next(
        decision for decision in report.decisions if decision.step_id == "build-biology"
    )
    assert statistics_decision.disposition is WorkflowResumeDisposition.RERUN
    assert statistics_decision.changed_input_keys == ("sample_metadata",)
    assert statistics_decision.reasons == ("input_checksums_changed",)
    assert biology_decision.disposition is WorkflowResumeDisposition.RERUN
    assert biology_decision.reasons == ("downstream_of_invalidated_step",)


def test_resume_workflow_reruns_from_incomplete_upstream_step_boundary(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "artifacts" / "resume-run"
    run_dir.mkdir(parents=True)

    fasta_text = ">sp|P1|PROT1\nMPEPTIDER"
    parsed_records = ({"accession": "P1", "sequence": "MPEPTIDER"},)
    parse_step = _step(
        step_id="parse-fasta",
        description="parse FASTA reference records",
        input_payloads={"config:fasta_text": fasta_text},
        output_payloads={"accepted_records": parsed_records},
        direct_input_keys=("fasta_text",),
        status="failed",
    )
    state = build_workflow_resume_state(
        workflow_id="sequence-to-biology",
        steps=(
            parse_step,
            _step(
                step_id="build-biology",
                description="assemble biology from parsed records",
                input_payloads={
                    "upstream:parse-fasta": parse_step.artifact.output_checksums
                },
                output_payloads={"biology_rows": ({"protein_id": "P1"},)},
                depends_on=("parse-fasta",),
            ),
        ),
    )
    write_workflow_resume_state(run_dir, state)

    report = resume_workflow(
        run_dir,
        WorkflowResumeConfig(
            workflow_id="sequence-to-biology",
            input_payloads={"fasta_text": fasta_text},
        ),
    )

    assert report.reused_step_ids == ()
    assert report.rerun_step_ids == ("parse-fasta", "build-biology")
    first_decision = report.decisions[0]
    second_decision = report.decisions[1]
    assert first_decision.reasons == ("step_not_completed",)
    assert second_decision.reasons == ("downstream_of_invalidated_step",)
