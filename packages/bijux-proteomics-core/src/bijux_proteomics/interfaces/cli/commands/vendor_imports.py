# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Vendor import CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.vendor_imports import run_spectronaut_import_command, run_openms_import_command

@click.command("spectronaut-import")
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
    "--precursor-quantity-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--protein-group-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--protein-group-quantity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def spectronaut_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    precursor_quantity_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    protein_group_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import one Spectronaut report with explicit precursor and protein-group review.'
    return run_spectronaut_import_command(result_tsv, config_path, summary_tsv_out, precursor_tsv_out, precursor_quantity_tsv_out, protein_group_tsv_out, protein_group_quantity_tsv_out, rejected_tsv_out, out_path)

@click.command("openms-import")
@click.argument(
    "idxml_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--feature-table",
    "feature_table_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--feature-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--rejected-feature-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def openms_import_command(
    idxml_path: Path,
    feature_table_path: Path,
    summary_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    feature_tsv_out: Path | None,
    rejected_feature_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import one OpenMS idXML bundle with practical exported feature evidence.'
    return run_openms_import_command(idxml_path, feature_table_path, summary_tsv_out, psm_tsv_out, protein_tsv_out, feature_tsv_out, rejected_feature_tsv_out, out_path)

COMMANDS = (
    spectronaut_import_command,
    openms_import_command,
)
