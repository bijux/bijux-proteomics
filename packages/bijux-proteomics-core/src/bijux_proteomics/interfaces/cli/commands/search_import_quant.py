# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Search import and quant benchmark CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.search_import_quant import (
    run_comet_import_command,
    run_diann_benchmark_command,
    run_diann_import_command,
    run_maxquant_benchmark_command,
    run_maxquant_import_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("comet-import")
@click.argument(
    "result_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def comet_import_command(
    result_path: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one Comet tabular or pepXML result file with explicit score review."""
    return run_comet_import_command(
        result_path,
        config_path,
        summary_tsv_out,
        canonical_psm_tsv_out,
        psm_tsv_out,
        rejected_tsv_out,
        out_path,
    )


@click.command("maxquant-import")
@click.argument(
    "evidence_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--peptides-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--protein-groups-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--evidence-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-group-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--lfq-candidate-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def maxquant_import_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    lfq_candidate_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one MaxQuant evidence, peptide, and protein-group bundle."""
    return run_maxquant_import_command(
        evidence_txt,
        peptides_txt,
        protein_groups_txt,
        config_path,
        summary_tsv_out,
        evidence_tsv_out,
        peptide_tsv_out,
        protein_group_tsv_out,
        lfq_candidate_tsv_out,
        rejected_tsv_out,
        out_path,
    )


@click.command("maxquant-benchmark")
@click.argument(
    "evidence_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--peptides-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--protein-groups-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--condition-a", type=str, default=None)
@click.option("--condition-b", type=str, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-identity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--filtering-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--lfq-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--differential-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def maxquant_benchmark_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    config_path: Path | None,
    design_tsv: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    summary_tsv_out: Path | None,
    protein_identity_tsv_out: Path | None,
    filtering_tsv_out: Path | None,
    lfq_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Benchmark governed MaxQuant import and LFQ behavior against source tables."""
    return run_maxquant_benchmark_command(
        evidence_txt,
        peptides_txt,
        protein_groups_txt,
        config_path,
        design_tsv,
        condition_a,
        condition_b,
        summary_tsv_out,
        protein_identity_tsv_out,
        filtering_tsv_out,
        lfq_tsv_out,
        differential_tsv_out,
        out_path,
    )


@click.command("diann-import")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--precursor-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-group-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one DIA-NN report with explicit precursor and protein-group review."""
    return run_diann_import_command(
        result_tsv,
        config_path,
        summary_tsv_out,
        precursor_tsv_out,
        protein_group_tsv_out,
        rejected_tsv_out,
        out_path,
    )


@click.command("diann-benchmark")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--count-comparisons-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-quantities-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_benchmark_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_quantities_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Benchmark governed DIA-NN import and protein matrix behavior against source rows."""
    return run_diann_benchmark_command(
        result_tsv,
        config_path,
        summary_tsv_out,
        count_comparisons_tsv_out,
        protein_quantities_tsv_out,
        out_path,
    )


COMMANDS = (
    comet_import_command,
    maxquant_import_command,
    maxquant_benchmark_command,
    diann_import_command,
    diann_benchmark_command,
)
