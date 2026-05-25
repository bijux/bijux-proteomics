# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""General program and FASTA Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405

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

def run_summarize_program(program_file: Path) -> None:
    program = ProgramSpec.load_json(program_file)
    click.echo(json.dumps(program_summary(program), sort_keys=True))

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

__all__ = ['run_program_template', 'run_summarize_program', 'run_sequence_checksum_command', 'run_fasta_parse_command', 'run_fasta_dedup_command', 'run_fasta_contaminants_command', 'run_fasta_filter_command', 'run_fasta_stats_command', 'run_fasta_profile_command']
