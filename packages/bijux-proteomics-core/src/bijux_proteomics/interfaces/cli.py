# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI for Bijux Proteomics domain and FASTA operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

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
