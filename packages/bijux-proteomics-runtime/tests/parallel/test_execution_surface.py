# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.parallel import (
    ParallelStep,
    ParallelStepFile,
    ParallelStepFileFormat,
    run_parallel_steps,
)


def _step_outputs(root: Path) -> tuple[ParallelStep, ...]:
    return (
        ParallelStep(
            step_id="parse-fasta",
            description="write parsed FASTA rows in fixed order",
            output_files=(
                ParallelStepFile(
                    path=str(root / "parse" / "accepted_records.tsv"),
                    format=ParallelStepFileFormat.TSV,
                    columns=("accession", "sequence"),
                    rows=(
                        {"accession": "P1", "sequence": "MPEPTIDER"},
                        {"accession": "P2", "sequence": "PEPTIDEK"},
                    ),
                ),
            ),
        ),
        ParallelStep(
            step_id="digest-targets",
            description="write target peptides after FASTA parsing",
            depends_on=("parse-fasta",),
            simulated_delay_ms=60,
            output_files=(
                ParallelStepFile(
                    path=str(root / "digest" / "targets.tsv"),
                    format=ParallelStepFileFormat.TSV,
                    columns=("peptide", "source"),
                    rows=(
                        {"peptide": "MPEPTIDER", "source": "P1"},
                        {"peptide": "PEPTIDEK", "source": "P2"},
                    ),
                ),
            ),
        ),
        ParallelStep(
            step_id="digest-decoys",
            description="write decoy peptides after FASTA parsing",
            depends_on=("parse-fasta",),
            simulated_delay_ms=5,
            output_files=(
                ParallelStepFile(
                    path=str(root / "digest" / "decoys.tsv"),
                    format=ParallelStepFileFormat.TSV,
                    columns=("peptide", "source"),
                    rows=(
                        {"peptide": "REDITPEPM", "source": "P1"},
                        {"peptide": "KEDITPEP", "source": "P2"},
                    ),
                ),
            ),
        ),
        ParallelStep(
            step_id="build-report",
            description="write stable combined report after digests complete",
            depends_on=("digest-decoys", "digest-targets"),
            output_files=(
                ParallelStepFile(
                    path=str(root / "reports" / "bundle.json"),
                    format=ParallelStepFileFormat.JSON,
                    json_payload={
                        "workflow_id": "sequence-to-digest",
                        "note": "row order is preserved from each upstream deterministic step",
                        "artifacts": [
                            "parse/accepted_records.tsv",
                            "digest/targets.tsv",
                            "digest/decoys.tsv",
                        ],
                    },
                ),
                ParallelStepFile(
                    path=str(root / "reports" / "summary.tsv"),
                    format=ParallelStepFileFormat.TSV,
                    columns=("artifact", "row_count"),
                    rows=(
                        {"artifact": "targets", "row_count": 2},
                        {"artifact": "decoys", "row_count": 2},
                    ),
                ),
            ),
        ),
    )


def _collect_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_run_parallel_steps_keeps_serial_and_parallel_outputs_byte_identical(
    tmp_path: Path,
) -> None:
    serial_root = tmp_path / "serial"
    parallel_root = tmp_path / "parallel"

    serial_report = run_parallel_steps(_step_outputs(serial_root), workers=1)
    parallel_report = run_parallel_steps(_step_outputs(parallel_root), workers=3)

    assert [group.step_ids for group in serial_report.groups] == [
        group.step_ids for group in parallel_report.groups
    ]
    assert [result.step_id for result in serial_report.step_results] == [
        result.step_id for result in parallel_report.step_results
    ]
    assert _collect_bytes(serial_root) == _collect_bytes(parallel_root)
    assert (
        (serial_root / "reports" / "summary.tsv").read_text(encoding="utf-8")
        == "artifact\trow_count\n"
        "targets\t2\n"
        "decoys\t2\n"
    )


def test_run_parallel_steps_refuses_duplicate_output_paths_across_steps(
    tmp_path: Path,
) -> None:
    shared_path = tmp_path / "shared.tsv"

    try:
        run_parallel_steps(
            (
                ParallelStep(
                    step_id="left",
                    description="write the shared file from the left branch",
                    output_files=(
                        ParallelStepFile(
                            path=str(shared_path),
                            format=ParallelStepFileFormat.TSV,
                            columns=("value",),
                            rows=({"value": "left"},),
                        ),
                    ),
                ),
                ParallelStep(
                    step_id="right",
                    description="write the shared file from the right branch",
                    output_files=(
                        ParallelStepFile(
                            path=str(shared_path),
                            format=ParallelStepFileFormat.TSV,
                            columns=("value",),
                            rows=({"value": "right"},),
                        ),
                    ),
                ),
            ),
            workers=2,
        )
    except ValueError as error:
        assert str(error) == "parallel steps cannot write the same output file path"
    else:
        raise AssertionError("duplicate output paths must be refused")
