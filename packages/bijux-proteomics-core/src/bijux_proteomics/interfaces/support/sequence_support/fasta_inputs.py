# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""FASTA loading and profile emission helpers for sequence workflows."""

from __future__ import annotations

from ..imports import *  # noqa: F401,F403
from ..output_protocol import _emit_json, _write_text_output


def _emit_fasta_profile(
    profile: FastaDatabaseProfile,
    *,
    out_path: Path | None,
    summary_tsv_out: Path | None,
    length_tsv_out: Path | None,
    organism_tsv_out: Path | None,
    invalid_sequence_tsv_out: Path | None,
) -> None:
    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_fasta_profile_summary_tsv(profile))
    if length_tsv_out is not None:
        _write_text_output(
            length_tsv_out, render_fasta_profile_length_distribution_tsv(profile)
        )
    if organism_tsv_out is not None:
        _write_text_output(
            organism_tsv_out, render_fasta_profile_organism_distribution_tsv(profile)
        )
    if invalid_sequence_tsv_out is not None:
        _write_text_output(
            invalid_sequence_tsv_out,
            render_fasta_profile_invalid_sequence_tsv(profile),
        )
    _emit_json(profile, out_path=out_path)


def _load_fasta_report(
    input_path: Path,
    *,
    mode: FastaParseMode,
    duplicate_accession_policy: DuplicateAccessionPolicy = DuplicateAccessionPolicy.REJECT,
    allow_rejected: bool,
) -> FastaParseReport:
    report = parse_fasta_document(
        input_path.read_text(),
        mode=mode,
        duplicate_accession_policy=duplicate_accession_policy,
    )
    if report.rejected_records and not allow_rejected:
        rejected = ", ".join(
            rejected.source_identifier for rejected in report.rejected_records
        )
        raise click.ClickException(
            f"FASTA input contains rejected records under {mode.value} mode: {rejected}"
        )
    return report
