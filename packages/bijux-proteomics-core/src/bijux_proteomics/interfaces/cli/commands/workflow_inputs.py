# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Input validation and experiment planning CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.workflow_inputs import (
    run_experiment_feasibility_command,
    run_format_convert_command,
    run_protocol_consistency_report_command,
    run_sample_sheet_repair_suggestions_command,
    run_summarize_command,
    run_validate_command,
)
from bijux_proteomics.interfaces.support.review_sequences_study import FastaParseMode
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _conversion_target_choice,
    _mode_choice,
    _validate_kind_choice,
)


@click.command("validate")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation output path.",
)
def validate_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    """Validate one FASTA, PSM TSV, MGF, mzML, design table, or modification registry input."""
    return run_validate_command(input_path, input_kind, mode, out_path)


@click.command("summarize")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON summary output path.",
)
def summarize_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    """Summarize one FASTA, PSM TSV, MGF, mzML, or design-table input."""
    return run_summarize_command(input_path, input_kind, mode, out_path)


@click.command("experiment-feasibility")
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default=None)
@click.option("--pairing-field", default=None)
@click.option("--timepoint-field", default=None)
@click.option("--ordered-timepoint", "ordered_timepoints", multiple=True)
@click.option(
    "--minimum-statistical-units-per-condition",
    default=2,
    show_default=True,
    type=int,
)
@click.option(
    "--valid-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--invalid-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-sizes-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missing-metadata-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--model-support-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def experiment_feasibility_command(
    design_path: Path,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str | None,
    pairing_field: str | None,
    timepoint_field: str | None,
    ordered_timepoints: tuple[str, ...],
    minimum_statistical_units_per_condition: int,
    valid_contrasts_tsv_out: Path | None,
    invalid_contrasts_tsv_out: Path | None,
    group_sizes_tsv_out: Path | None,
    missing_metadata_tsv_out: Path | None,
    model_support_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Report what a study design can and cannot support before analysis."""
    return run_experiment_feasibility_command(
        design_path,
        condition_a,
        condition_b,
        batch_field,
        pairing_field,
        timepoint_field,
        ordered_timepoints,
        minimum_statistical_units_per_condition,
        valid_contrasts_tsv_out,
        invalid_contrasts_tsv_out,
        group_sizes_tsv_out,
        missing_metadata_tsv_out,
        model_support_tsv_out,
        out_path,
    )


@click.command("protocol-consistency-report")
@click.argument(
    "protocol_context_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--psm",
    "psm_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--proteins-fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--reporter-table",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ptm-evidence-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--diagnostics-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def protocol_consistency_report_command(
    protocol_context_tsv: Path,
    spectra_path: Path | None,
    psm_path: Path | None,
    proteins_fasta: Path | None,
    reporter_table: Path | None,
    ptm_evidence_tsv: Path | None,
    diagnostics_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Check whether observed evidence matches the declared lab protocol context."""
    return run_protocol_consistency_report_command(
        protocol_context_tsv,
        spectra_path,
        psm_path,
        proteins_fasta,
        reporter_table,
        ptm_evidence_tsv,
        diagnostics_tsv_out,
        out_path,
    )


@click.command("sample-sheet-repair-suggestions")
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--observed-sample-id",
    "observed_sample_ids",
    multiple=True,
    help="Observed sample id from analysis data. Repeat for multiple ids.",
)
@click.option(
    "--observed-run-id",
    "observed_run_ids",
    multiple=True,
    help="Observed run id from analysis data. Repeat for multiple ids.",
)
@click.option(
    "--observed-sample-id-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional text file with one observed sample id per line.",
)
@click.option(
    "--observed-run-id-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional text file with one observed run id per line.",
)
@click.option(
    "--suggestions-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def sample_sheet_repair_suggestions_command(
    design_path: Path,
    observed_sample_ids: tuple[str, ...],
    observed_run_ids: tuple[str, ...],
    observed_sample_id_file: Path | None,
    observed_run_id_file: Path | None,
    suggestions_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Suggest exact sample-sheet repairs without rewriting study metadata."""
    return run_sample_sheet_repair_suggestions_command(
        design_path,
        observed_sample_ids,
        observed_run_ids,
        observed_sample_id_file,
        observed_run_id_file,
        suggestions_tsv_out,
        out_path,
    )


@click.command("format-convert")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option("--to", "target_format", type=_conversion_target_choice(), required=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the converted normalized output.",
)
def format_convert_command(
    input_path: Path,
    input_kind: str,
    target_format: str,
    out_path: Path,
) -> None:
    """Convert one supported input into a normalized Bijux output surface."""
    return run_format_convert_command(input_path, input_kind, target_format, out_path)


COMMANDS = (
    validate_command,
    summarize_command,
    experiment_feasibility_command,
    protocol_consistency_report_command,
    sample_sheet_repair_suggestions_command,
    format_convert_command,
)
