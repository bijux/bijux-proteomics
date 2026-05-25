# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Search import and FragPipe benchmark CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.search_import_fragpipe import run_psm_contaminants_command, run_fragpipe_import_command, run_fragpipe_benchmark_command, run_sage_import_command

@click.command("psm-contaminants")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--contaminant-prefix",
    "contaminant_prefixes",
    multiple=True,
    default=("CON__",),
    show_default=True,
    help="Protein-reference prefixes that mark contaminant evidence.",
)
@click.option("--run-id-column", default=None)
@click.option("--intensity-column", default=None)
@click.option(
    "--burden-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON contaminant-match report output path.",
)
def psm_contaminants_command(
    input_tsv: Path,
    contaminant_prefixes: tuple[str, ...],
    run_id_column: str | None,
    intensity_column: str | None,
    burden_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Separate contaminant-carrying peptide-spectrum matches from target-only evidence.'
    return run_psm_contaminants_command(input_tsv, contaminant_prefixes, run_id_column, intensity_column, burden_tsv_out, protein_tsv_out, out_path)

@click.command("fragpipe-import")
@click.argument("psm_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--peptide-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--protein-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--quant-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--peptide-review-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-review-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--open-search-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-quantity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def fragpipe_import_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    quant_tsv: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    peptide_review_tsv_out: Path | None,
    protein_review_tsv_out: Path | None,
    open_search_tsv_out: Path | None,
    protein_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import one FragPipe result bundle with explicit PSM, peptide, and protein review.'
    return run_fragpipe_import_command(psm_tsv, peptide_tsv, protein_tsv, quant_tsv, summary_tsv_out, canonical_psm_tsv_out, psm_tsv_out, peptide_review_tsv_out, protein_review_tsv_out, open_search_tsv_out, protein_quantity_tsv_out, rejected_tsv_out, out_path)

@click.command("fragpipe-benchmark")
@click.argument("psm_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--peptide-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--protein-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--count-comparisons-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-groups-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--psm-qvalues-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-qvalues-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def fragpipe_benchmark_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_groups_tsv_out: Path | None,
    psm_qvalues_tsv_out: Path | None,
    peptide_qvalues_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Benchmark governed FragPipe import behavior against the source FragPipe bundle.'
    return run_fragpipe_benchmark_command(psm_tsv, peptide_tsv, protein_tsv, summary_tsv_out, count_comparisons_tsv_out, protein_groups_tsv_out, psm_qvalues_tsv_out, peptide_qvalues_tsv_out, out_path)

@click.command("sage-import")
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
def sage_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import one Sage result table with explicit score, q-value, and modification review.'
    return run_sage_import_command(result_tsv, config_path, summary_tsv_out, canonical_psm_tsv_out, psm_tsv_out, rejected_tsv_out, out_path)

COMMANDS = (
    psm_contaminants_command,
    fragpipe_import_command,
    fragpipe_benchmark_command,
    sage_import_command,
)
