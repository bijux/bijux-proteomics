# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Peptide chemistry Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    FragmentIonSeries,
    Path,
    approximate_peptide_isotope_envelope,
    build_fragment_ion_review_report,
    build_modification_localization_advisory,
    build_modified_peptide,
    build_peptide_charge_state,
    build_peptide_elemental_composition,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
    click,
    load_modification_registry,
    predict_peptide_isotope_envelopes,
    render_fragment_ion_report_tsv,
    render_isotope_envelopes_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    PeptideDigestionMode,
    build_peptide_database_lookup_report,
    build_peptide_property_report,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.sequence_support.digestion_parameters import (
    _resolve_cli_protease_rule,
)
from bijux_proteomics.interfaces.support.sequence_support.fasta_inputs import (
    _load_fasta_report,
)
from bijux_proteomics.interfaces.support.targeted_selection_io.protein_support import (
    _load_protein_group_map,
)


def run_peptide_index_command(
    input_fasta: Path,
    peptides: tuple[str, ...],
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    il_equivalent: bool,
    protein_group_map: Path | None,
    out_path: Path | None,
) -> None:
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        report = _load_fasta_report(
            input_fasta,
            mode=FastaParseMode(mode),
            allow_rejected=False,
        )
        group_map = (
            _load_protein_group_map(protein_group_map)
            if protein_group_map is not None
            else {}
        )
        lookup = build_peptide_database_lookup_report(
            peptides,
            report.accepted_records,
            protease=protease_rule,
            missed_cleavages=missed_cleavages,
            digestion_mode=PeptideDigestionMode(digestion_mode),
            treat_isoleucine_as_leucine=il_equivalent,
            protein_group_by_accession=group_map,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    _emit_json(
        {
            "input_record_count": report.total_records,
            "query_peptide_count": len(peptides),
            "protease": protease_rule.name,
            "custom_protease": custom_specification,
            "digestion_mode": digestion_mode,
            "missed_cleavages": missed_cleavages,
            "il_equivalent": il_equivalent,
            "protein_group_map_supplied": protein_group_map is not None,
            "report": lookup.to_dict(),
        },
        out_path=out_path,
    )


def run_peptide_mass_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    isotope_peaks: int,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        composition = build_peptide_elemental_composition(
            peptide,
            registry=registry,
        )
        charge_state = build_peptide_charge_state(
            peptide,
            charge=charge,
            registry=registry,
        )
        envelope = approximate_peptide_isotope_envelope(
            peptide,
            charge=charge,
            peak_count=isotope_peaks,
            registry=registry,
        )
        localization = build_modification_localization_advisory(
            peptide,
            registry=registry,
        )
        fragments = calculate_fragment_ions(
            peptide,
            charges=(charge,),
            series=tuple(FragmentIonSeries(series) for series in fragment_series),
            include_neutral_losses=include_neutral_losses,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    payload = {
        "canonical_notation": canonicalize_modified_peptide(peptide, registry=registry),
        "elemental_composition": composition.to_dict(),
        "charge_state": charge_state.to_dict(),
        "isotope_envelope": envelope.to_dict(),
        "localization": localization.to_dict(),
        "fragment_ion_count": len(fragments),
        "fragments": [fragment.to_dict() for fragment in fragments],
    }
    _emit_json(payload, out_path=out_path)


def run_isotope_envelope_command(
    sequence: str,
    modifications: tuple[str, ...],
    charges: tuple[int, ...],
    max_isotope_index: int,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        composition = build_peptide_elemental_composition(
            peptide,
            registry=registry,
        )
        envelopes = predict_peptide_isotope_envelopes(
            peptide,
            charges=charges,
            max_isotope_index=max_isotope_index,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if tsv_out is not None:
        _write_text_output(tsv_out, render_isotope_envelopes_tsv(envelopes))

    payload = {
        "canonical_notation": peptide.canonical_notation,
        "elemental_composition": composition.to_dict(),
        "charges": list(charges),
        "max_isotope_index": max_isotope_index,
        "envelopes": [envelope.to_dict() for envelope in envelopes],
        "tsv_out": str(tsv_out) if tsv_out else None,
    }
    _emit_json(payload, out_path=out_path)


def run_fragment_ions_command(
    sequence: str,
    modifications: tuple[str, ...],
    charges: tuple[int, ...],
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        report = build_fragment_ion_review_report(
            peptide,
            charges=tuple(charges),
            series=tuple(
                FragmentIonSeries(series_name) for series_name in fragment_series
            ),
            include_neutral_losses=include_neutral_losses,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if tsv_out is not None:
        _write_text_output(tsv_out, render_fragment_ion_report_tsv(report))

    payload = report.to_dict()
    payload["tsv_out"] = str(tsv_out) if tsv_out else None
    _emit_json(payload, out_path=out_path)


def run_peptide_properties_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    registry_path: Path | None,
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
        report = build_peptide_property_report(
            sequence,
            modification_assignments=modifications,
            charge=charge,
            protease=protease_rule,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    payload = report.to_dict()
    payload["custom_protease"] = custom_specification
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_peptide_index_command",
    "run_peptide_mass_command",
    "run_isotope_envelope_command",
    "run_fragment_ions_command",
    "run_peptide_properties_command",
]
