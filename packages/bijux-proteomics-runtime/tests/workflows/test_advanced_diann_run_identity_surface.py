# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path

from bijux_proteomics.workflow import AdvancedDiannWorkflowConfig
from bijux_proteomics_runtime.workflows import (
    build_advanced_diann_runtime_run_identity,
    dry_run_resumable_advanced_diann_workflow,
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
        if reader.fieldnames is None:
            raise ValueError(f"{source_path.name!r} must include a header row")
        fieldnames = list(reader.fieldnames)
        with target_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(
                target,
                fieldnames=fieldnames,
                delimiter="\t",
            )
            writer.writeheader()
            for row in reader:
                if row["Protein.Group"] == protein_group_id:
                    row["Q.Value"] = q_value
                writer.writerow(row)


def test_advanced_diann_run_identity_matches_between_dry_run_and_runtime(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_identity_runtime",
        condition_a="control",
        condition_b="treatment",
    )

    dry_run = dry_run_resumable_advanced_diann_workflow(config)
    runtime = run_resumable_advanced_diann_workflow(config)

    assert dry_run.workflow_type == "advanced_diann_runtime"
    assert dry_run.workflow_id == dry_run.run_id
    assert runtime.workflow_id == runtime.run_id
    assert dry_run.run_identity == runtime.run_identity
    assert dry_run.run_id == runtime.run_id


def test_advanced_diann_run_identity_ignores_output_directory(
    tmp_path: Path,
) -> None:
    left = build_advanced_diann_runtime_run_identity(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "left",
            condition_a="control",
            condition_b="treatment",
        )
    )
    right = build_advanced_diann_runtime_run_identity(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "right",
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert left.run_id == right.run_id
    assert left.fingerprint_sha256 == right.fingerprint_sha256
    assert {entry.input_name for entry in left.input_checksums} >= {
        "result_tsv_sha256",
        "design_tsv_sha256",
        "proteins_fasta_sha256",
    }
    assert all("output_dir" not in entry.input_name for entry in left.input_checksums)


def test_advanced_diann_run_identity_changes_when_semantic_parameter_changes(
    tmp_path: Path,
) -> None:
    baseline = build_advanced_diann_runtime_run_identity(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_identity_baseline",
            condition_a="control",
            condition_b="treatment",
        )
    )
    threshold_variant = build_advanced_diann_runtime_run_identity(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_identity_threshold",
            max_q_value=0.05,
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert baseline.run_id != threshold_variant.run_id
    assert (
        baseline.parameter_fingerprint_sha256
        != threshold_variant.parameter_fingerprint_sha256
    )


def test_advanced_diann_run_identity_changes_when_input_checksum_changes(
    tmp_path: Path,
) -> None:
    variant_path = tmp_path / "diann_input_variant.tsv"
    _write_q_value_variant(
        source_path=_workflow_fixture("diann_advanced_report.tsv"),
        target_path=variant_path,
        protein_group_id="PG005",
        q_value="0.02",
    )
    baseline = build_advanced_diann_runtime_run_identity(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_identity_input_baseline",
            condition_a="control",
            condition_b="treatment",
        )
    )
    mutated = build_advanced_diann_runtime_run_identity(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=variant_path,
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_identity_input_variant",
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert baseline.run_id != mutated.run_id
    assert baseline.parameter_fingerprint_sha256 == mutated.parameter_fingerprint_sha256
    assert baseline.input_checksums != mutated.input_checksums
