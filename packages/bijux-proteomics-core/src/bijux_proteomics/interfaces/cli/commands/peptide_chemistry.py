# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Peptide chemistry CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("peptide-index")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--peptide",
    "peptides",
    multiple=True,
    required=True,
    help="Repeat for each peptide or modified peptide query to index.",
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
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
@click.option("--missed-cleavages", type=int, default=0, show_default=True)
@click.option(
    "--digestion-mode",
    type=_digestion_mode_choice(),
    default=PeptideDigestionMode.FULL.value,
    show_default=True,
)
@click.option(
    "--il-equivalent/--exact-il",
    default=False,
    show_default=True,
    help="Optionally collapse isoleucine and leucine during peptide lookup.",
)
@click.option(
    "--protein-group-map",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional TSV with accession and protein_group columns.",
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def peptide_index_command(
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
    'Index peptide queries against a digested FASTA database.'
    return run_peptide_index_command(input_fasta, peptides, mode, protease, custom_protease, custom_protease_name, missed_cleavages, digestion_mode, il_equivalent, protein_group_map, out_path)

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

@click.command("peptide-mass")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option("--charge", type=int, default=2, show_default=True)
@click.option(
    "--fragment-series",
    multiple=True,
    type=_fragment_series_choice(),
    default=("a", "b", "y"),
    show_default=True,
)
@click.option("--include-neutral-losses", is_flag=True, default=False)
@click.option("--isotope-peaks", type=int, default=6, show_default=True)
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
def peptide_mass_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    isotope_peaks: int,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    'Emit peptide chemistry diagnostics for one sequence plus optional modifications.'
    return run_peptide_mass_command(sequence, modifications, charge, fragment_series, include_neutral_losses, isotope_peaks, registry_path, out_path)

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

@click.command("isotope-envelope")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option(
    "--charge",
    "charges",
    multiple=True,
    type=int,
    default=(2,),
    show_default=True,
)
@click.option(
    "--max-isotope-index",
    type=int,
    default=5,
    show_default=True,
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
    help="Optional isotope envelope TSV output path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def isotope_envelope_command(
    sequence: str,
    modifications: tuple[str, ...],
    charges: tuple[int, ...],
    max_isotope_index: int,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Predict M+0 through M+n isotope envelopes for one peptide.'
    return run_isotope_envelope_command(sequence, modifications, charges, max_isotope_index, registry_path, tsv_out, out_path)

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

@click.command("fragment-ions")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option(
    "--charge",
    "charges",
    multiple=True,
    type=int,
    default=(1, 2, 3),
    show_default=True,
)
@click.option(
    "--fragment-series",
    multiple=True,
    type=_fragment_series_choice(),
    default=("a", "b", "y"),
    show_default=True,
)
@click.option("--include-neutral-losses", is_flag=True, default=False)
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
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fragment_ions_command(
    sequence: str,
    modifications: tuple[str, ...],
    charges: tuple[int, ...],
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Emit one dedicated theoretical fragment-ion review report.'
    return run_fragment_ions_command(sequence, modifications, charges, fragment_series, include_neutral_losses, registry_path, tsv_out, out_path)

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

@click.command("peptide-properties")
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
def peptide_properties_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    'Emit peptide property diagnostics for filtering and review.'
    return run_peptide_properties_command(sequence, modifications, charge, protease, custom_protease, custom_protease_name, registry_path, out_path)

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

COMMANDS = (
    peptide_index_command,
    peptide_mass_command,
    isotope_envelope_command,
    fragment_ions_command,
    peptide_properties_command,
)
