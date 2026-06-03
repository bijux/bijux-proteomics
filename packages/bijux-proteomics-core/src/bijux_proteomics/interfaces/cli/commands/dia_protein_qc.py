# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""DIA protein-matrix and QC CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.dia_protein_qc import run_diann_protein_matrix_command, run_spectronaut_protein_matrix_command, run_diann_run_qc_command, run_diann_library_coverage_command

@click.command("diann-protein-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--peptide-rollup",
    type=click.Choice([method.value for method in DiaPeptideRollupMethod]),
    default=DiaPeptideRollupMethod.MAX.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=click.Choice([kind.value for kind in DiaProteinMatrixTargetKind]),
    default=DiaProteinMatrixTargetKind.PROTEIN_GROUP.value,
    show_default=True,
)
@click.option(
    "--shared-peptides",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option(
    "--protein-rollup",
    type=click.Choice([method.value for method in DiaProteinRollupMethod]),
    default=DiaProteinRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--rollup-evidence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_protein_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    peptide_rollup: str,
    target_kind: str,
    shared_peptides: str,
    protein_rollup: str,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    rollup_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build DIA peptide and protein matrices from one DIA-NN report.'
    return run_diann_protein_matrix_command(result_tsv, config_path, include_decoys, max_q_value, peptide_rollup, target_kind, shared_peptides, protein_rollup, summary_tsv_out, peptide_tsv_out, protein_tsv_out, rollup_evidence_tsv_out, out_path)

@click.command("spectronaut-protein-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--peptide-rollup",
    type=click.Choice([method.value for method in DiaPeptideRollupMethod]),
    default=DiaPeptideRollupMethod.MAX.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=click.Choice([kind.value for kind in DiaProteinMatrixTargetKind]),
    default=DiaProteinMatrixTargetKind.PROTEIN_GROUP.value,
    show_default=True,
)
@click.option(
    "--shared-peptides",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option(
    "--protein-rollup",
    type=click.Choice([method.value for method in DiaProteinRollupMethod]),
    default=DiaProteinRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--rollup-evidence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def spectronaut_protein_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    peptide_rollup: str,
    target_kind: str,
    shared_peptides: str,
    protein_rollup: str,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    rollup_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build DIA peptide and protein matrices from one Spectronaut report.'
    return run_spectronaut_protein_matrix_command(result_tsv, config_path, include_decoys, max_q_value, peptide_rollup, target_kind, shared_peptides, protein_rollup, summary_tsv_out, peptide_tsv_out, protein_tsv_out, rollup_evidence_tsv_out, out_path)

@click.command("diann-run-qc")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--run-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--intensity-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--correlation-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--outlier-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_run_qc_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    run_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    outlier_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build DIA run-level QC from one DIA-NN report.'
    return run_diann_run_qc_command(result_tsv, config_path, include_decoys, max_q_value, summary_tsv_out, run_tsv_out, intensity_tsv_out, correlation_tsv_out, outlier_tsv_out, out_path)

@click.command("diann-library-coverage")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "library_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--shared-peptides",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sample-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--condition-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--outside-library-peptide-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--outside-library-protein-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_library_coverage_command(
    result_tsv: Path,
    library_path: Path,
    design_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    shared_peptides: str,
    summary_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    condition_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    outside_library_peptide_tsv_out: Path | None,
    outside_library_protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Compare DIA-NN observations against spectral-library peptide and protein scope.'
    return run_diann_library_coverage_command(result_tsv, library_path, design_path, include_decoys, max_q_value, shared_peptides, summary_tsv_out, sample_tsv_out, condition_tsv_out, peptide_tsv_out, protein_tsv_out, outside_library_peptide_tsv_out, outside_library_protein_tsv_out, out_path)

COMMANDS = (
    diann_protein_matrix_command,
    spectronaut_protein_matrix_command,
    diann_run_qc_command,
    diann_library_coverage_command,
)
