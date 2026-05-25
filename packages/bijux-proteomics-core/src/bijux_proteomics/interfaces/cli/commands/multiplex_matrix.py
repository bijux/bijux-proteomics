# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Multiplex matrix and normalization CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.multiplex_matrix import run_multiplex_validate_metadata_command, run_tmt_reporter_matrix_command, run_tmt_interference_command, run_tmt_normalize_command

@click.command("validate-metadata")
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--channel-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--duplicate-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--missing-condition-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def multiplex_validate_metadata_command(
    design_path: Path,
    summary_tsv_out: Path | None,
    channel_tsv_out: Path | None,
    duplicate_tsv_out: Path | None,
    missing_condition_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Validate multiplex sample metadata mappings from the design table.'
    return run_multiplex_validate_metadata_command(design_path, summary_tsv_out, channel_tsv_out, duplicate_tsv_out, missing_condition_tsv_out, out_path)

@click.command("tmt-reporter-matrix")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--channel-mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--channel-totals-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_reporter_matrix_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    channel_mapping_tsv_out: Path | None,
    channel_totals_tsv_out: Path | None,
    peptide_matrix_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import TMT reporter-ion search results and build sample-channel matrices.'
    return run_tmt_reporter_matrix_command(input_tsv, design_path, source_kind, row_id_column, peptide_column, protein_refs_column, multiplex_group_column, default_multiplex_group, protein_separator, channel_columns, summary_tsv_out, channel_mapping_tsv_out, channel_totals_tsv_out, peptide_matrix_tsv_out, protein_matrix_tsv_out, out_path)

@click.command("tmt-interference")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--interference-threshold",
    default=0.3,
    show_default=True,
    type=float,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--interference-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--observation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--filtered-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--channel-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_interference_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    interference_threshold: float,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    interference_column: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    observation_tsv_out: Path | None,
    filtered_tsv_out: Path | None,
    channel_summary_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Review TMT reporter-ion isolation interference and export filter ledgers.'
    return run_tmt_interference_command(input_tsv, design_path, source_kind, interference_threshold, row_id_column, peptide_column, protein_refs_column, multiplex_group_column, default_multiplex_group, interference_column, protein_separator, channel_columns, summary_tsv_out, observation_tsv_out, filtered_tsv_out, channel_summary_tsv_out, out_path)

@click.command("tmt-normalize")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--method",
    type=_tmt_normalization_method_choice(),
    default=TmtNormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--transform-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_normalize_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    method: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    transform_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    peptide_matrix_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Normalize TMT reporter-channel evidence and export before/after review ledgers.'
    return run_tmt_normalize_command(input_tsv, design_path, source_kind, method, row_id_column, peptide_column, protein_refs_column, multiplex_group_column, default_multiplex_group, protein_separator, channel_columns, summary_tsv_out, transform_tsv_out, distribution_tsv_out, peptide_matrix_tsv_out, protein_matrix_tsv_out, out_path)

COMMANDS = (
    multiplex_validate_metadata_command,
    tmt_reporter_matrix_command,
    tmt_interference_command,
    tmt_normalize_command,
)
