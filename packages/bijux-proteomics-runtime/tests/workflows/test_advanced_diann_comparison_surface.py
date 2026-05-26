# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bijux_proteomics.workflow import AdvancedDiannWorkflowConfig
from bijux_proteomics_runtime.workflows import (
    AdvancedDiannClaimComparisonState,
    AdvancedDiannProteinComparisonState,
    AdvancedDiannRejectedRowComparisonState,
    AdvancedDiannRuntimeStage,
    compare_advanced_diann_runtime_outputs,
    run_resumable_advanced_diann_workflow,
)


def _workflow_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "workflow"
        / name
    )


def _write_q_value_variant(
    *,
    source_path: Path,
    target_path: Path,
    protein_group_id: str,
    q_value: str,
) -> None:
    with source_path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        with target_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(
                target,
                fieldnames=reader.fieldnames,
                delimiter="\t",
            )
            writer.writeheader()
            for row in reader:
                if row["Protein.Group"] == protein_group_id:
                    row["Q.Value"] = q_value
                writer.writerow(row)


def test_compare_advanced_diann_runtime_outputs_reports_threshold_drift(
    tmp_path: Path,
) -> None:
    variant_path = tmp_path / "diann_threshold_variant.tsv"
    _write_q_value_variant(
        source_path=_workflow_fixture("diann_advanced_report.tsv"),
        target_path=variant_path,
        protein_group_id="PG005",
        q_value="0.02",
    )
    low_threshold = run_resumable_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=variant_path,
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_q001",
            max_q_value=0.01,
            condition_a="control",
            condition_b="treatment",
        )
    )
    high_threshold = run_resumable_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=variant_path,
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_q005",
            max_q_value=0.05,
            condition_a="control",
            condition_b="treatment",
        )
    )

    report = compare_advanced_diann_runtime_outputs(low_threshold, high_threshold)

    assert report.equivalent is False
    assert [entry.parameter_name for entry in report.parameter_changes] == ["max_q_value"]
    assert [entry.protein_group_id for entry in report.changed_proteins] == ["PG005"]
    assert report.changed_proteins[0].left_state is AdvancedDiannProteinComparisonState.ABSENT
    assert (
        report.changed_proteins[0].right_state
        is AdvancedDiannProteinComparisonState.ACCEPTED
    )
    assert [entry.claim_id for entry in report.changed_claims] == ["protein-claim:PG005"]
    assert report.changed_claims[0].left_state is AdvancedDiannClaimComparisonState.ABSENT
    assert (
        report.changed_claims[0].right_state
        is AdvancedDiannClaimComparisonState.SUPPORTED
    )
    assert len(report.changed_rejected_rows) == 6
    assert {
        entry.precursor_id for entry in report.changed_rejected_rows
    } == {
        "raw_C1_PEPEEE_2",
        "raw_C2_PEPEEE_2",
        "raw_C3_PEPEEE_2",
        "raw_T1_PEPEEE_2",
        "raw_T2_PEPEEE_2",
        "raw_T3_PEPEEE_2",
    }
    assert all(
        entry.left_state is AdvancedDiannRejectedRowComparisonState.REJECTED
        and entry.right_state is AdvancedDiannRejectedRowComparisonState.RETAINED
        for entry in report.changed_rejected_rows
    )


def test_compare_advanced_diann_runtime_outputs_is_equivalent_for_matching_runs(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_baseline",
        condition_a="control",
        condition_b="treatment",
    )
    left = run_resumable_advanced_diann_workflow(config)
    right = run_resumable_advanced_diann_workflow(
        config.model_copy(update={"output_dir": tmp_path / "advanced_diann_baseline_copy"})
    )

    report = compare_advanced_diann_runtime_outputs(left, right)

    assert left.run_id == right.run_id
    assert left.run_identity == right.run_identity
    assert report.equivalent is True
    assert report.parameter_changes == ()
    assert report.changed_proteins == ()
    assert report.changed_claims == ()
    assert report.changed_rejected_rows == ()


def test_compare_advanced_diann_runtime_outputs_requires_completed_runs(
    tmp_path: Path,
) -> None:
    interrupted = run_resumable_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_interrupted",
            condition_a="control",
            condition_b="treatment",
        ),
        through_stage=AdvancedDiannRuntimeStage.MATRICES,
    )
    completed = run_resumable_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_completed",
            condition_a="control",
            condition_b="treatment",
        )
    )

    with pytest.raises(
        ValueError,
        match="advanced dia-nn comparison requires completed runtime runs",
    ):
        compare_advanced_diann_runtime_outputs(interrupted, completed)
