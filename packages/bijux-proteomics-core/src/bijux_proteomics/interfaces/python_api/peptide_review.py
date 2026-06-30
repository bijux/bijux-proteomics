# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Peptide review Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    build_modification_resolution_report,
    build_search_engine_modified_peptide_report,
    click,
    load_modification_registry,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    build_precursor_mass_error_report,
    render_precursor_mass_error_distribution_tsv,
    render_precursor_mass_error_observations_tsv,
    render_precursor_mass_error_summary_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    build_peptide_detectability_report,
    render_peptide_detectability_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.sequence_support.digestion_parameters import (
    _resolve_cli_protease_rule,
)
from bijux_proteomics.interfaces.support.sequence_support.input_resolution import (
    _load_precursor_mass_error_queries,
)


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


__all__ = [
    "run_peptide_detectability_command",
    "run_precursor_mass_error_command",
    "run_modified_peptide_parse_command",
    "run_modification_resolve_command",
]
