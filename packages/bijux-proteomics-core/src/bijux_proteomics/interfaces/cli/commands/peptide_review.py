# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Peptide review CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("peptide-detectability")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option("--charge", type=int, default=2, show_default=True)
@click.option("--protease", default="trypsin", show_default=True)
@click.option(
    "--custom-protease",
    default=None,
    help=(
        "Custom rule such as 'after=KR;block_next=P', "
        "'before=D;block_previous=P', or "
        "'pattern=(?<!P)(?P<site>D);cut_before=site'."
    ),
)
@click.option(
    "--custom-protease-name",
    default="custom",
    show_default=True,
    help="Stable name recorded for a custom protease rule.",
)
@click.option(
    "--uniqueness-class",
    type=click.Choice([entry.value for entry in PeptideUniquenessClass]),
    default=None,
    help="Optional database uniqueness class from the owned uniqueness index.",
)
@click.option(
    "--uniqueness-score",
    type=float,
    default=None,
    help="Optional explicit uniqueness score from 0.0 to 1.0.",
)
@click.option(
    "--observed-psm-count",
    type=int,
    default=None,
    help="Optional observed PSM count to boost detectability with real evidence.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional detectability TSV output path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def peptide_detectability_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    uniqueness_class: str | None,
    uniqueness_score: float | None,
    observed_psm_count: int | None,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Score peptide observability from owned sequence and chemistry semantics.'
    return run_peptide_detectability_command(sequence, modifications, charge, protease, custom_protease, custom_protease_name, uniqueness_class, uniqueness_score, observed_psm_count, registry_path, tsv_out, out_path)

def run_peptide_detectability_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    uniqueness_class: str | None,
    uniqueness_score: float | None,
    observed_psm_count: int | None,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_peptide_detectability_report(
            sequence,
            modification_assignments=modifications,
            charge=charge,
            protease=protease_rule,
            registry=registry,
            uniqueness_class=uniqueness_class,
            uniqueness_score=uniqueness_score,
            observed_psm_count=observed_psm_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if tsv_out is not None:
        _write_text_output(tsv_out, render_peptide_detectability_tsv(report))

    payload = report.to_dict()
    payload["custom_protease"] = custom_specification
    payload["tsv_out"] = str(tsv_out) if tsv_out else None
    _emit_json(payload, out_path=out_path)

@click.command("precursor-mass-error")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--observed-mz-column", default="observed_mz", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--max-isotope-offset", type=int, default=3, show_default=True)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--observations-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ppm-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--isotope-distribution-tsv-out",
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
def precursor_mass_error_command(
    input_tsv: Path,
    peptide_column: str,
    observed_mz_column: str,
    charge_column: str,
    spectrum_id_column: str,
    max_isotope_offset: int,
    registry_path: Path | None,
    summary_tsv_out: Path | None,
    observations_tsv_out: Path | None,
    ppm_distribution_tsv_out: Path | None,
    charge_distribution_tsv_out: Path | None,
    isotope_distribution_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Report precursor mass error from peptide plus observed-m/z tables.'
    return run_precursor_mass_error_command(input_tsv, peptide_column, observed_mz_column, charge_column, spectrum_id_column, max_isotope_offset, registry_path, summary_tsv_out, observations_tsv_out, ppm_distribution_tsv_out, charge_distribution_tsv_out, isotope_distribution_tsv_out, out_path)

def run_precursor_mass_error_command(
    input_tsv: Path,
    peptide_column: str,
    observed_mz_column: str,
    charge_column: str,
    spectrum_id_column: str,
    max_isotope_offset: int,
    registry_path: Path | None,
    summary_tsv_out: Path | None,
    observations_tsv_out: Path | None,
    ppm_distribution_tsv_out: Path | None,
    charge_distribution_tsv_out: Path | None,
    isotope_distribution_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        queries = _load_precursor_mass_error_queries(
            input_tsv,
            peptide_column=peptide_column,
            observed_mz_column=observed_mz_column,
            charge_column=charge_column,
            spectrum_id_column=spectrum_id_column,
        )
        report = build_precursor_mass_error_report(
            queries,
            registry=registry,
            max_isotope_offset=max_isotope_offset,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_precursor_mass_error_summary_tsv(report),
        )
    if observations_tsv_out is not None:
        _write_text_output(
            observations_tsv_out,
            render_precursor_mass_error_observations_tsv(report.observations),
        )
    if ppm_distribution_tsv_out is not None:
        _write_text_output(
            ppm_distribution_tsv_out,
            render_precursor_mass_error_distribution_tsv(
                report.ppm_error_distribution,
                distribution_name="abs_ppm",
            ),
        )
    if charge_distribution_tsv_out is not None:
        _write_text_output(
            charge_distribution_tsv_out,
            render_precursor_mass_error_distribution_tsv(
                report.charge_distribution,
                distribution_name="charge",
            ),
        )
    if isotope_distribution_tsv_out is not None:
        _write_text_output(
            isotope_distribution_tsv_out,
            render_precursor_mass_error_distribution_tsv(
                report.isotope_offset_distribution,
                distribution_name="recommended_isotope_offset",
            ),
        )

    payload = report.to_dict()
    payload["input_row_count"] = len(queries)
    payload["summary_tsv_out"] = str(summary_tsv_out) if summary_tsv_out else None
    payload["observations_tsv_out"] = (
        str(observations_tsv_out) if observations_tsv_out else None
    )
    payload["ppm_distribution_tsv_out"] = (
        str(ppm_distribution_tsv_out) if ppm_distribution_tsv_out else None
    )
    payload["charge_distribution_tsv_out"] = (
        str(charge_distribution_tsv_out) if charge_distribution_tsv_out else None
    )
    payload["isotope_distribution_tsv_out"] = (
        str(isotope_distribution_tsv_out) if isotope_distribution_tsv_out else None
    )
    _emit_json(payload, out_path=out_path)

@click.command("modified-peptide-parse")
@click.argument("notation")
@click.option(
    "--dialect",
    type=_modified_peptide_dialect_choice(),
    required=True,
    help="Search-engine peptide notation dialect to normalize.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def modified_peptide_parse_command(
    notation: str,
    dialect: str,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    'Normalize one search-engine modified peptide notation.'
    return run_modified_peptide_parse_command(notation, dialect, registry_path, out_path)

def run_modified_peptide_parse_command(
    notation: str,
    dialect: str,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_search_engine_modified_peptide_report(
            notation,
            dialect=dialect,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    _emit_json(report.to_dict(), out_path=out_path)

@click.command("modification-resolve")
@click.argument("token")
@click.option(
    "--residue",
    default=None,
    help="Optional residue for residue-compatibility review.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def modification_resolve_command(
    token: str,
    residue: str | None,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    'Resolve one modification token against builtin or custom registries.'
    return run_modification_resolve_command(token, residue, registry_path, out_path)

def run_modification_resolve_command(
    token: str,
    residue: str | None,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_modification_resolution_report(
            token,
            residue=residue,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    _emit_json(report.to_dict(), out_path=out_path)

COMMANDS = (
    peptide_detectability_command,
    precursor_mass_error_command,
    modified_peptide_parse_command,
    modification_resolve_command,
)
