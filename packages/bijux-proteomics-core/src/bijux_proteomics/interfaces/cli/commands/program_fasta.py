# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""General program and FASTA CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("program-template")
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
    'Write a starter program manifest.'
    return run_program_template(program_id, name, objective, target_id, target_name, sequence, organism, mechanism, out_path)

def run_program_template(
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

@click.command("summarize-program")
@click.argument("program_file", type=click.Path(exists=True, path_type=Path))
def summarize_program(program_file: Path) -> None:
    'Print a compact summary for a program document.'
    return run_summarize_program(program_file)

def run_summarize_program(program_file: Path) -> None:
    program = ProgramSpec.load_json(program_file)
    click.echo(json.dumps(program_summary(program), sort_keys=True))

@click.command("sequence-checksum")
@click.option(
    "--sequence", required=True, help="Protein sequence to normalize and hash."
)
def sequence_checksum_command(sequence: str) -> None:
    'Emit the normalized sequence checksum for one protein sequence string.'
    return run_sequence_checksum_command(sequence)

def run_sequence_checksum_command(sequence: str) -> None:
    normalized = "".join(
        character for character in sequence.upper() if not character.isspace()
    )
    _emit_json(
        {
            "normalized_sequence": normalized,
            "residue_count": len(normalized),
            "sequence_checksum": sequence_checksum(sequence),
        }
    )

@click.command("fasta-parse")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_parse_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
) -> None:
    'Parse FASTA input and emit normalized acceptance and rejection details.'
    return run_fasta_parse_command(input_fasta, mode, duplicate_accession_policy, out_path)

def run_fasta_parse_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
) -> None:
    report = parse_fasta_document(
        input_fasta.read_text(),
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
    )
    _emit_json(report, out_path=out_path)

@click.command("fasta-dedup")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
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
    duplicate_accession_policy: str,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    'Deduplicate FASTA records by accession and normalized sequence digest.'
    return run_fasta_dedup_command(input_fasta, mode, duplicate_accession_policy, out_fasta, report_out)

def run_fasta_dedup_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=False,
    )
    deduplicated, dedup_report = deduplicate_fasta_records(report.accepted_records)
    out_fasta.write_text(render_fasta_records(deduplicated))
    _emit_json(dedup_report, out_path=report_out)

@click.command("fasta-contaminants")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--include-builtin/--no-include-builtin",
    default=True,
    show_default=True,
    help="Append the owned built-in contaminant panel.",
)
@click.option(
    "--contaminant-fasta",
    "contaminant_fastas",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
    help="Optional external contaminant FASTA path to append after relabeling.",
)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the combined target-plus-contaminant FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON build report output path.",
)
def fasta_contaminants_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    include_builtin: bool,
    contaminant_fastas: tuple[Path, ...],
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    'Append labeled contaminant proteins to one target FASTA database.'
    return run_fasta_contaminants_command(input_fasta, mode, duplicate_accession_policy, include_builtin, contaminant_fastas, out_fasta, report_out)

def run_fasta_contaminants_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    include_builtin: bool,
    contaminant_fastas: tuple[Path, ...],
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    target_report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
    )
    external_records: list[NormalizedProteinRecord] = []
    for contaminant_fasta in contaminant_fastas:
        contaminant_report = _load_fasta_report(
            contaminant_fasta,
            mode=FastaParseMode(mode),
            allow_rejected=False,
            duplicate_accession_policy=DuplicateAccessionPolicy(
                duplicate_accession_policy
            ),
        )
        external_records.extend(contaminant_report.accepted_records)
    combined, build_report = append_contaminant_database(
        target_report.accepted_records,
        include_builtin=include_builtin,
        external_contaminant_records=tuple(external_records),
    )
    out_fasta.write_text(render_fasta_records(combined))
    _emit_json(build_report, out_path=report_out)

@click.command("fasta-filter")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option("--min-length", type=int, default=None)
@click.option("--max-length", type=int, default=None)
@click.option(
    "--accession-pattern",
    default=None,
    help="Regular expression over canonical accession.",
)
@click.option(
    "--organism", default=None, help="Exact organism filter, case-insensitive."
)
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
    duplicate_accession_policy: str,
    min_length: int | None,
    max_length: int | None,
    accession_pattern: str | None,
    organism: str | None,
    exclude_contaminants: bool,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    'Filter FASTA records while emitting explicit exclusion counts.'
    return run_fasta_filter_command(input_fasta, mode, duplicate_accession_policy, min_length, max_length, accession_pattern, organism, exclude_contaminants, out_fasta, report_out)

def run_fasta_filter_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    min_length: int | None,
    max_length: int | None,
    accession_pattern: str | None,
    organism: str | None,
    exclude_contaminants: bool,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
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

@click.command("fasta-stats")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_stats_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
) -> None:
    'Report FASTA record, composition, residue, duplication, and contaminant metrics.'
    return run_fasta_stats_command(input_fasta, mode, duplicate_accession_policy, out_path)

def run_fasta_stats_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=True,
    )
    stats = build_fasta_stats(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )
    _emit_json(stats, out_path=out_path)

@click.command("fasta-profile")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON profile output path.",
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional summary TSV output path.",
)
@click.option(
    "--length-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional length-distribution TSV output path.",
)
@click.option(
    "--organism-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional organism-distribution TSV output path.",
)
@click.option(
    "--invalid-sequence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional invalid-sequence TSV output path.",
)
def fasta_profile_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
    summary_tsv_out: Path | None,
    length_tsv_out: Path | None,
    organism_tsv_out: Path | None,
    invalid_sequence_tsv_out: Path | None,
) -> None:
    'Profile one FASTA database with composition, organism, and rejection ledgers.'
    return run_fasta_profile_command(input_fasta, mode, duplicate_accession_policy, out_path, summary_tsv_out, length_tsv_out, organism_tsv_out, invalid_sequence_tsv_out)

def run_fasta_profile_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
    summary_tsv_out: Path | None,
    length_tsv_out: Path | None,
    organism_tsv_out: Path | None,
    invalid_sequence_tsv_out: Path | None,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=True,
    )
    profile = build_fasta_database_profile(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )
    _emit_fasta_profile(
        profile,
        out_path=out_path,
        summary_tsv_out=summary_tsv_out,
        length_tsv_out=length_tsv_out,
        organism_tsv_out=organism_tsv_out,
        invalid_sequence_tsv_out=invalid_sequence_tsv_out,
    )

COMMANDS = (
    program_template,
    summarize_program,
    sequence_checksum_command,
    fasta_parse_command,
    fasta_dedup_command,
    fasta_contaminants_command,
    fasta_filter_command,
    fasta_stats_command,
    fasta_profile_command,
)
