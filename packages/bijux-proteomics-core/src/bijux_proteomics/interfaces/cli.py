# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI for Bijux Proteomics domain and FASTA operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from bijux_proteomics.chemistry import (
    approximate_peptide_isotope_envelope,
    build_modification_localization_advisory,
    build_modified_peptide,
    build_peptide_charge_state,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
    FragmentIonSeries,
    load_modification_registry,
)
from bijux_proteomics.digestion import (
    PeptideDigestionMode,
    build_digest_manifest,
    digest_protein_records,
    export_peptides_jsonl,
    export_peptides_parquet,
    export_peptides_tsv,
    get_protease_rule,
    peptide_export_fingerprint,
)
from bijux_proteomics.formats import (
    build_mzml_collection_summary,
    build_normalized_run_bundle,
    convert_proteomics_format,
    FormatConversionTarget,
    parse_experimental_design_table,
    parse_mzml,
    ProteomicsFormatKind,
    validate_proteomics_input,
)
from bijux_proteomics.identification import (
    apply_q_values,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    build_peptide_summary_report,
    build_protein_summary_report,
    build_psm_summary_report,
    build_search_result_provenance_manifest,
    export_psm_jsonl,
    export_psm_tsv,
    FdrPolicy,
    filter_psms_by_fdr,
    parse_psm_tsv,
    SearchResultColumnMapping,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.search_adapters import (
    build_search_adapter_conformance_report,
    build_search_adapter_capability_matrix,
    build_search_adapter_provenance_manifest,
    compare_search_result_reports,
    get_search_adapter_manifest,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
    SearchAdapterKind,
    ScoreOrientation,
    validate_search_parameters,
)
from bijux_proteomics.programs import ProgramSpec, create_program_spec, program_summary
from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    FastaParseMode,
    FastaParseReport,
    build_fasta_provenance_manifest,
    build_fasta_stats,
    deduplicate_fasta_records,
    filter_fasta_records,
    generate_decoy_records,
    parse_fasta_document,
    render_fasta_records,
    sequence_checksum,
    validate_target_decoy_database,
)
from bijux_proteomics.spectra import (
    annotate_spectrum_fragments,
    build_spectrum_collection_summary,
    build_spectrum_metrics,
    build_spectrum_plot_payload,
    build_spectrum_provenance_manifest,
    export_spectrum_annotation_tsv,
    parse_mgf,
)


def _emit_json(payload: Any, *, out_path: Path | None = None) -> None:
    if hasattr(payload, "to_stable_json"):
        rendered = payload.to_stable_json()
    else:
        rendered = json.dumps(payload, indent=2, sort_keys=True)
    if out_path is not None:
        out_path.write_text(rendered + "\n")
    click.echo(rendered)


def _load_fasta_report(
    input_path: Path,
    *,
    mode: FastaParseMode,
    allow_rejected: bool,
) -> FastaParseReport:
    report = parse_fasta_document(input_path.read_text(), mode=mode)
    if report.rejected_records and not allow_rejected:
        rejected = ", ".join(
            rejected.source_identifier for rejected in report.rejected_records
        )
        raise click.ClickException(
            f"FASTA input contains rejected records under {mode.value} mode: {rejected}"
        )
    return report


def _mode_choice() -> click.Choice:
    return click.Choice([mode.value for mode in FastaParseMode], case_sensitive=False)


def _decoy_mode_choice() -> click.Choice:
    return click.Choice(
        [mode.value for mode in DecoyGenerationMode],
        case_sensitive=False,
    )


def _digestion_mode_choice() -> click.Choice:
    return click.Choice(
        [mode.value for mode in PeptideDigestionMode],
        case_sensitive=False,
    )


def _export_format_choice() -> click.Choice:
    return click.Choice(["tsv", "jsonl", "parquet"], case_sensitive=False)


def _fragment_series_choice() -> click.Choice:
    return click.Choice([series.value for series in FragmentIonSeries], case_sensitive=False)


def _validate_kind_choice() -> click.Choice:
    return click.Choice(
        ["auto", "fasta", "psm", "mgf", "mzml", "mod-registry", "design-table"],
        case_sensitive=False,
    )


def _conversion_target_choice() -> click.Choice:
    return click.Choice([target.value for target in FormatConversionTarget], case_sensitive=False)


def _search_adapter_choice() -> click.Choice:
    return click.Choice([adapter.value for adapter in SearchAdapterKind], case_sensitive=False)


def _score_orientation_choice() -> click.Choice:
    return click.Choice([orientation.value for orientation in ScoreOrientation], case_sensitive=False)


def _build_psm_mapping(
    *,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
) -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id=spectrum_id_column,
        peptide=peptide_column,
        charge=charge_column,
        score=score_column,
        q_value=q_value_column,
        protein_refs=protein_refs_column,
        decoy_label=decoy_label_column,
        protein_separator=protein_separator,
    )


def _build_decoy_policy(
    *,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
) -> TargetDecoyLabelPolicy:
    return TargetDecoyLabelPolicy(
        protein_prefix=decoy_prefix,
        protein_suffix=decoy_suffix,
    )


def _default_psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def _infer_input_kind(input_path: Path, explicit_kind: str) -> str:
    if explicit_kind != "auto":
        return explicit_kind
    suffix = input_path.suffix.lower()
    if suffix in {".fasta", ".fa", ".faa"}:
        return "fasta"
    if suffix == ".mgf":
        return "mgf"
    if suffix == ".mzml":
        return "mzml"
    if path.name.endswith(".design.tsv") or path.name.endswith(".design.csv"):
        return "design-table"
    if suffix == ".tsv":
        return "psm"
    if suffix == ".json":
        return "mod-registry"
    raise click.ClickException(
        f"cannot infer input kind for {input_path.name!r}; use --kind fasta, psm, mgf, mzml, design-table, or mod-registry"
    )


@click.group()
def cli() -> None:
    """Manage program manifests and protein-sequence operations."""


@cli.command("program-template")
@click.option("--program-id", required=True, help="Stable program identifier.")
@click.option("--name", required=True, help="Program name.")
@click.option("--objective", required=True, help="Scientific objective.")
@click.option("--target-id", required=True, help="Stable target identifier.")
@click.option("--target-name", required=True, help="Target name.")
@click.option("--sequence", required=True, help="Reference amino-acid sequence.")
@click.option("--organism", required=True, help="Source organism.")
@click.option("--mechanism", required=True, help="Working target hypothesis.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the JSON document.",
)
def program_template(
    program_id: str,
    name: str,
    objective: str,
    target_id: str,
    target_name: str,
    sequence: str,
    organism: str,
    mechanism: str,
    out_path: Path,
) -> None:
    """Write a starter program manifest."""
    program = create_program_spec(
        program_id=program_id,
        name=name,
        objective=objective,
        target_id=target_id,
        target_name=target_name,
        sequence=sequence,
        organism=organism,
        mechanism=mechanism,
    )
    program.save_json(out_path)
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("summarize-program")
@click.argument("program_file", type=click.Path(exists=True, path_type=Path))
def summarize_program(program_file: Path) -> None:
    """Print a compact summary for a program document."""
    program = ProgramSpec.load_json(program_file)
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("sequence-checksum")
@click.option("--sequence", required=True, help="Protein sequence to normalize and hash.")
def sequence_checksum_command(sequence: str) -> None:
    """Emit the normalized sequence checksum for one protein sequence string."""
    normalized = "".join(character for character in sequence.upper() if not character.isspace())
    _emit_json(
        {
            "normalized_sequence": normalized,
            "residue_count": len(normalized),
            "sequence_checksum": sequence_checksum(sequence),
        }
    )


@cli.command("fasta-parse")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_parse_command(input_fasta: Path, mode: str, out_path: Path | None) -> None:
    """Parse FASTA input and emit normalized acceptance and rejection details."""
    report = parse_fasta_document(input_fasta.read_text(), mode=FastaParseMode(mode))
    _emit_json(report, out_path=out_path)


@cli.command("fasta-dedup")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the deduplicated FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_dedup_command(
    input_fasta: Path,
    mode: str,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Deduplicate FASTA records by accession and normalized sequence digest."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    deduplicated, dedup_report = deduplicate_fasta_records(report.accepted_records)
    out_fasta.write_text(render_fasta_records(deduplicated))
    _emit_json(dedup_report, out_path=report_out)


@cli.command("fasta-filter")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option("--min-length", type=int, default=None)
@click.option("--max-length", type=int, default=None)
@click.option("--accession-pattern", default=None, help="Regular expression over canonical accession.")
@click.option("--organism", default=None, help="Exact organism filter, case-insensitive.")
@click.option("--exclude-contaminants", is_flag=True, default=False)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the filtered FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_filter_command(
    input_fasta: Path,
    mode: str,
    min_length: int | None,
    max_length: int | None,
    accession_pattern: str | None,
    organism: str | None,
    exclude_contaminants: bool,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Filter FASTA records while emitting explicit exclusion counts."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    filtered, filter_report = filter_fasta_records(
        report.accepted_records,
        min_length=min_length,
        max_length=max_length,
        accession_pattern=accession_pattern,
        organism=organism,
        exclude_contaminants=exclude_contaminants,
    )
    out_fasta.write_text(render_fasta_records(filtered))
    _emit_json(filter_report, out_path=report_out)


@cli.command("fasta-stats")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_stats_command(input_fasta: Path, mode: str, out_path: Path | None) -> None:
    """Report FASTA record, residue, duplication, and contaminant metrics."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=True,
    )
    stats = build_fasta_stats(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )
    _emit_json(stats, out_path=out_path)


@cli.command("fasta-provenance")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option("--operation", default="fasta-parse", show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the provenance manifest JSON.",
)
def fasta_provenance_command(
    input_fasta: Path,
    mode: str,
    operation: str,
    out_path: Path,
) -> None:
    """Write a provenance manifest for one FASTA processing step."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=True,
    )
    manifest = build_fasta_provenance_manifest(
        operation=operation,
        source_path=input_fasta,
        parse_mode=FastaParseMode(mode),
        input_record_count=report.total_records,
        accepted_record_count=len(report.accepted_records),
        rejected_record_count=len(report.rejected_records),
        output_record_count=len(report.accepted_records),
        parameters={"operation": operation},
    )
    _emit_json(manifest, out_path=out_path)


@cli.command("fasta-decoy")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option("--decoy-mode", type=_decoy_mode_choice(), default=DecoyGenerationMode.REVERSE.value, show_default=True)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option("--seed", type=int, default=17, show_default=True)
@click.option("--decoys-only", is_flag=True, default=False, help="Write only decoy records instead of target+decoy output.")
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the generated target/decoy FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation report output path.",
)
def fasta_decoy_command(
    input_fasta: Path,
    mode: str,
    decoy_mode: str,
    prefix: str,
    seed: int,
    decoys_only: bool,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Generate target/decoy FASTA output and validate the result."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    decoys = generate_decoy_records(
        report.accepted_records,
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
    )
    output_records = decoys if decoys_only else (*report.accepted_records, *decoys)
    out_fasta.write_text(render_fasta_records(tuple(output_records)))
    validation = validate_target_decoy_database(tuple(output_records), prefix=prefix)
    _emit_json(validation, out_path=report_out)


@cli.command("target-decoy-validate")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def target_decoy_validate_command(
    input_fasta: Path,
    mode: str,
    prefix: str,
    out_path: Path | None,
) -> None:
    """Validate target/decoy pairing completeness for a FASTA collection."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    validation = validate_target_decoy_database(report.accepted_records, prefix=prefix)
    _emit_json(validation, out_path=out_path)


@cli.command("digest")
@click.argument("input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
@click.option("--protease", default="trypsin", show_default=True)
@click.option("--missed-cleavages", type=int, default=0, show_default=True)
@click.option("--digestion-mode", type=_digestion_mode_choice(), default=PeptideDigestionMode.FULL.value, show_default=True)
@click.option("--min-length", type=int, default=1, show_default=True)
@click.option("--max-length", type=int, default=None)
@click.option("--min-mass", type=float, default=None)
@click.option("--max-mass", type=float, default=None)
@click.option("--format", "export_format", type=_export_format_choice(), default="tsv", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), required=True)
@click.option("--manifest-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
def digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    export_format: str,
    out_path: Path,
    manifest_out: Path | None,
) -> None:
    """Digest FASTA records into peptide exports."""
    try:
        protease_rule = get_protease_rule(protease)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    peptides = digest_protein_records(
        report.accepted_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode(digestion_mode),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )

    try:
        if export_format == "tsv":
            export_peptides_tsv(peptides, out_path)
        elif export_format == "jsonl":
            export_peptides_jsonl(peptides, out_path)
        else:
            export_peptides_parquet(peptides, out_path)
    except (RuntimeError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    manifest = build_digest_manifest(
        peptides=peptides,
        protease=protease_rule.name,
        digestion_mode=PeptideDigestionMode(digestion_mode),
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")

    _emit_json(
        {
            "input_record_count": report.total_records,
            "output_peptide_count": len(peptides),
            "protease": protease_rule.name,
            "digestion_mode": digestion_mode,
            "export_format": export_format,
            "output_sha256": peptide_export_fingerprint(peptides),
            "output_path": str(out_path),
        }
    )


@cli.command("peptide-mass")
@click.argument("sequence")
@click.option("--mod", "modifications", multiple=True, help="Modification assignment like Oxidation@3 or Acetyl@n-term.")
@click.option("--charge", type=int, default=2, show_default=True)
@click.option(
    "--fragment-series",
    multiple=True,
    type=_fragment_series_choice(),
    default=("b", "y"),
    show_default=True,
)
@click.option("--include-neutral-losses", is_flag=True, default=False)
@click.option("--isotope-peaks", type=int, default=4, show_default=True)
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
    """Emit peptide chemistry diagnostics for one sequence plus optional modifications."""
    try:
        registry = load_modification_registry(registry_path) if registry_path is not None else None
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
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
        "charge_state": charge_state.to_dict(),
        "isotope_envelope": envelope.to_dict(),
        "localization": localization.to_dict(),
        "fragment_ion_count": len(fragments),
        "fragments": [fragment.to_dict() for fragment in fragments],
    }
    _emit_json(payload, out_path=out_path)


@cli.command("psm-inspect")
@click.argument("input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option("--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def psm_inspect_command(
    input_tsv: Path,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Inspect a generic PSM TSV and emit normalized summaries."""
    try:
        mapping = _build_psm_mapping(
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        normalized = apply_q_values(report.accepted_records)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(normalized, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(normalized, tsv_out)

    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=report,
        decoy_policy=decoy_policy,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")

    payload = {
        "accepted_rows": len(report.accepted_records),
        "rejected_rows": len(report.rejected_rows),
        "psm_summary": build_psm_summary_report(normalized).to_dict(),
        "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
        "protein_summary": build_protein_summary_report(normalized).to_dict(),
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fdr")
@click.argument("input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--threshold", type=float, default=0.01, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option("--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--audit-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--calibration-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def fdr_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    audit_out: Path | None,
    calibration_out: Path | None,
    out_path: Path | None,
) -> None:
    """Apply basic target-decoy FDR and emit filtered PSM summaries."""
    try:
        mapping = _build_psm_mapping(
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(accepted, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(accepted, tsv_out)

    fdr_policy = FdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=parse_report,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    audit_trail = build_fdr_audit_trail(
        parse_report.accepted_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    calibration_plot = build_calibration_plot_data(
        parse_report.accepted_records,
        score_orientation=score_orientation,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    if audit_out is not None:
        audit_out.write_text(audit_trail.to_stable_json() + "\n")
    if calibration_out is not None:
        calibration_out.write_text(calibration_plot.to_stable_json() + "\n")

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted),
        "psm_summary": build_psm_summary_report(accepted).to_dict(),
        "peptide_summary": build_peptide_summary_report(accepted).to_dict(),
        "protein_summary": build_protein_summary_report(accepted).to_dict(),
        "audit_trail": audit_trail.to_dict(),
        "calibration_plot": calibration_plot.to_dict(),
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-stats")
@click.argument("input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_stats_command(
    input_mgf: Path,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Summarize one MGF collection."""
    report = parse_mgf(input_mgf)
    summary = build_spectrum_collection_summary(report)
    provenance = build_spectrum_provenance_manifest(source_path=input_mgf, parse_report=report)
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "summary": summary.to_dict(),
        "provenance": provenance.to_dict(),
        "metrics": [build_spectrum_metrics(spectrum).to_dict() for spectrum in report.accepted_spectra],
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-annotate")
@click.argument("input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--peptide", required=True)
@click.option("--spectrum-id", default=None, help="Optional target spectrum id; defaults to the first accepted spectrum.")
@click.option("--tolerance-da", type=float, default=0.02, show_default=True)
@click.option("--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--plot-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON annotation output path.",
)
def spectrum_annotate_command(
    input_mgf: Path,
    peptide: str,
    spectrum_id: str | None,
    tolerance_da: float,
    tsv_out: Path | None,
    plot_out: Path | None,
    out_path: Path | None,
) -> None:
    """Annotate one spectrum against a peptide sequence."""
    report = parse_mgf(input_mgf)
    if not report.accepted_spectra:
        raise click.ClickException("MGF input does not contain an accepted spectrum to annotate")
    if spectrum_id is None:
        spectrum = report.accepted_spectra[0]
    else:
        try:
            spectrum = next(item for item in report.accepted_spectra if item.spectrum_id == spectrum_id)
        except StopIteration as exc:
            raise click.ClickException(f"unknown spectrum id {spectrum_id!r}") from exc
    try:
        annotation = annotate_spectrum_fragments(
            spectrum,
            peptide=peptide,
            tolerance_da=tolerance_da,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    plot_payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
    if tsv_out is not None:
        export_spectrum_annotation_tsv(annotation, tsv_out)
    if plot_out is not None:
        plot_out.write_text(plot_payload.to_stable_json() + "\n")
    payload = {
        "annotation": annotation.to_dict(),
        "plot_payload": plot_payload.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("validate")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--kind", "input_kind", type=_validate_kind_choice(), default="auto", show_default=True)
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
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
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = validate_proteomics_input(
            input_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)


@cli.command("summarize")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--kind", "input_kind", type=_validate_kind_choice(), default="auto", show_default=True)
@click.option("--mode", type=_mode_choice(), default=FastaParseMode.STRICT.value, show_default=True)
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
    resolved_kind = _infer_input_kind(input_path, input_kind)
    if resolved_kind == "fasta":
        report = parse_fasta_document(input_path.read_text(), mode=FastaParseMode(mode))
        payload = {
            "input_kind": resolved_kind,
            "summary": build_fasta_stats(report.accepted_records).to_dict(),
            "rejected_records": len(report.rejected_records),
        }
    elif resolved_kind == "psm":
        report = parse_psm_tsv(input_path, mapping=_default_psm_mapping())
        normalized = apply_q_values(report.accepted_records)
        payload = {
            "input_kind": resolved_kind,
            "psm_summary": build_psm_summary_report(normalized).to_dict(),
            "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
            "protein_summary": build_protein_summary_report(normalized).to_dict(),
            "rejected_rows": len(report.rejected_rows),
        }
    elif resolved_kind == "mgf":
        report = parse_mgf(input_path)
        payload = {
            "input_kind": resolved_kind,
            "summary": build_spectrum_collection_summary(report).to_dict(),
            "metrics": [build_spectrum_metrics(spectrum).to_dict() for spectrum in report.accepted_spectra],
        }
    elif resolved_kind == "mzml":
        report = parse_mzml(input_path)
        payload = {
            "input_kind": resolved_kind,
            "metadata": report.metadata.to_dict(),
            "summary": build_mzml_collection_summary(report).to_dict(),
            "metrics": [build_spectrum_metrics(spectrum).to_dict() for spectrum in report.accepted_spectra],
        }
    elif resolved_kind == "design-table":
        report = parse_experimental_design_table(input_path)
        payload = {
            "input_kind": resolved_kind,
            "accepted_entries": len(report.accepted_entries),
            "rejected_rows": len(report.rejected_rows),
            "instruments": sorted(
                {
                    entry.instrument
                    for entry in report.accepted_entries
                    if entry.instrument is not None
                }
            ),
            "search_engines": sorted(
                {
                    entry.search_engine
                    for entry in report.accepted_entries
                    if entry.search_engine is not None
                }
            ),
        }
    else:
        raise click.ClickException(
            "summarize currently supports fasta, psm, mgf, mzml, and design-table inputs"
        )
    _emit_json(payload, out_path=out_path)


@cli.command("format-convert")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--kind", "input_kind", type=_validate_kind_choice(), default="auto", show_default=True)
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
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = convert_proteomics_format(
            input_path=input_path,
            output_path=out_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
            target_format=FormatConversionTarget(target_format),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report)


@cli.command("bundle-run")
@click.option("--spectra", "spectra_path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out-dir",
    "out_dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
    help="Directory where the normalized run bundle should be written.",
)
def bundle_run_command(
    spectra_path: Path,
    identifications_path: Path | None,
    design_path: Path | None,
    out_dir: Path,
) -> None:
    """Build one normalized run bundle from spectra, IDs, and optional design metadata."""
    try:
        manifest = build_normalized_run_bundle(
            bundle_dir=out_dir,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            design_path=design_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(manifest)


@cli.group("search-adapter")
def search_adapter_group() -> None:
    """Inspect and normalize search-engine-specific result tables."""


@search_adapter_group.command("inspect")
@click.option("--adapter", "adapter_name", type=_search_adapter_choice(), default=None)
def search_adapter_inspect_command(adapter_name: str | None) -> None:
    """Inspect one adapter manifest or the full capability matrix."""
    if adapter_name is None:
        payload = {
            "capabilities": [row.to_dict() for row in build_search_adapter_capability_matrix()],
        }
        _emit_json(payload)
        return
    manifest = get_search_adapter_manifest(SearchAdapterKind(adapter_name))
    _emit_json(manifest)


@search_adapter_group.command("params")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def search_adapter_params_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    """Parse one supported search-engine parameter file."""
    try:
        payload = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("validate-config")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def search_adapter_validate_config_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    """Validate one supported search-engine parameter file."""
    try:
        parameters = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
        payload = validate_search_parameters(parameters)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("normalize")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mapping-json", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--adapter-version", default=None)
@click.option("--config", "config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON normalization output path.",
)
def search_adapter_normalize_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    adapter_version: str | None,
    config_path: Path | None,
    jsonl_out: Path | None,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Normalize one engine-specific search-result table into stable PSM records."""
    mapping = None
    if mapping_json is not None:
        mapping = SearchResultColumnMapping.model_validate_json(mapping_json.read_text())
    try:
        report = normalize_search_results_with_adapter(
            source_path=input_path,
            adapter_kind=SearchAdapterKind(adapter_name),
            mapping=mapping,
        )
        provenance = build_search_adapter_provenance_manifest(
            source_path=input_path,
            normalization_report=report,
            adapter_version=adapter_version,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    if jsonl_out is not None:
        export_psm_jsonl(report.normalized_records, jsonl_out)
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "adapter": report.adapter_manifest.to_dict(),
        "accepted_rows": len(report.parse_report.accepted_records),
        "rejected_rows": len(report.parse_report.rejected_rows),
        "normalized_records": [record.to_dict() for record in report.normalized_records],
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("compare")
@click.argument("left_adapter_name", type=_search_adapter_choice())
@click.argument("left_input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("right_adapter_name", type=_search_adapter_choice())
@click.argument("right_input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--left-mapping-json", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--right-mapping-json", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def search_adapter_compare_command(
    left_adapter_name: str,
    left_input_path: Path,
    right_adapter_name: str,
    right_input_path: Path,
    left_mapping_json: Path | None,
    right_mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    """Compare two normalized adapter outputs on a shared score scale."""
    left_mapping = (
        SearchResultColumnMapping.model_validate_json(left_mapping_json.read_text())
        if left_mapping_json is not None
        else None
    )
    right_mapping = (
        SearchResultColumnMapping.model_validate_json(right_mapping_json.read_text())
        if right_mapping_json is not None
        else None
    )
    try:
        left_report = normalize_search_results_with_adapter(
            source_path=left_input_path,
            adapter_kind=SearchAdapterKind(left_adapter_name),
            mapping=left_mapping,
        )
        right_report = normalize_search_results_with_adapter(
            source_path=right_input_path,
            adapter_kind=SearchAdapterKind(right_adapter_name),
            mapping=right_mapping,
        )
        payload = compare_search_result_reports(left_report, right_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("conformance")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mapping-json", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None)
def search_adapter_conformance_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    """Run the built-in adapter conformance checks on one search-result table."""
    mapping = (
        SearchResultColumnMapping.model_validate_json(mapping_json.read_text())
        if mapping_json is not None
        else None
    )
    try:
        normalization_report = normalize_search_results_with_adapter(
            source_path=input_path,
            adapter_kind=SearchAdapterKind(adapter_name),
            mapping=mapping,
        )
        payload = build_search_adapter_conformance_report(normalization_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)
