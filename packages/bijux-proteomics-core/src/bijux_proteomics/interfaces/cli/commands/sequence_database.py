# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""FASTA provenance, decoy, and digestion CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.sequence_database import (
    run_digest_command,
    run_fasta_decoy_command,
    run_fasta_provenance_command,
    run_target_decoy_validate_command,
    run_theoretical_digest_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("fasta-provenance")
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
    duplicate_accession_policy: str,
    operation: str,
    out_path: Path,
) -> None:
    """Write a provenance manifest for one FASTA processing step."""
    return run_fasta_provenance_command(
        input_fasta, mode, duplicate_accession_policy, operation, out_path
    )


@click.command("fasta-decoy")
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
    "--decoy-mode",
    type=_decoy_mode_choice(),
    default=DecoyGenerationMode.REVERSE.value,
    show_default=True,
)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option("--seed", type=int, default=17, show_default=True)
@click.option(
    "--decoys-only",
    is_flag=True,
    default=False,
    help="Write only decoy records instead of target+decoy output.",
)
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
@click.option(
    "--manifest-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON manifest output path.",
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
    manifest_out: Path | None,
) -> None:
    """Generate target/decoy FASTA output and validate the result."""
    return run_fasta_decoy_command(
        input_fasta,
        mode,
        decoy_mode,
        prefix,
        seed,
        decoys_only,
        out_fasta,
        report_out,
        manifest_out,
    )


@click.command("target-decoy-validate")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
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
    return run_target_decoy_validate_command(input_fasta, mode, prefix, out_path)


@click.command("digest")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option("--min-length", type=int, default=1, show_default=True)
@click.option("--max-length", type=int, default=None)
@click.option("--min-mass", type=float, default=None)
@click.option("--max-mass", type=float, default=None)
@click.option(
    "--format",
    "export_format",
    type=_export_format_choice(),
    default="tsv",
    show_default=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), required=True
)
@click.option(
    "--manifest-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--peptide-protein-table-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    export_format: str,
    out_path: Path,
    manifest_out: Path | None,
    peptide_protein_table_out: Path | None,
) -> None:
    """Digest FASTA records into peptide exports."""
    return run_digest_command(
        input_fasta,
        mode,
        protease,
        custom_protease,
        custom_protease_name,
        missed_cleavages,
        digestion_mode,
        min_length,
        max_length,
        min_mass,
        max_mass,
        export_format,
        out_path,
        manifest_out,
        peptide_protein_table_out,
    )


@click.command("theoretical-digest")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option("--min-length", type=int, default=1, show_default=True)
@click.option("--max-length", type=int, default=None)
@click.option("--min-mass", type=float, default=None)
@click.option("--max-mass", type=float, default=None)
@click.option(
    "--static-mod",
    "static_modifications",
    multiple=True,
    help="Repeat for each static modification name or controlled id.",
)
@click.option(
    "--variable-mod",
    "variable_modifications",
    multiple=True,
    help="Repeat for each variable modification name or controlled id.",
)
@click.option(
    "--modification-registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--allow-isotopic-labels/--disallow-isotopic-labels",
    default=False,
    show_default=True,
)
@click.option(
    "--allowed-label-family",
    "allowed_label_families",
    multiple=True,
    help="Repeat for each allowed isotopic label family.",
)
@click.option(
    "--max-variants-per-peptide",
    type=int,
    default=128,
    show_default=True,
)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
)
def theoretical_digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    static_modifications: tuple[str, ...],
    variable_modifications: tuple[str, ...],
    registry_path: Path | None,
    allow_isotopic_labels: bool,
    allowed_label_families: tuple[str, ...],
    max_variants_per_peptide: int,
    out_dir: Path,
) -> None:
    """Build the governed theoretical digest TSV bundle."""
    return run_theoretical_digest_command(
        input_fasta,
        mode,
        protease,
        custom_protease,
        custom_protease_name,
        missed_cleavages,
        digestion_mode,
        min_length,
        max_length,
        min_mass,
        max_mass,
        static_modifications,
        variable_modifications,
        registry_path,
        allow_isotopic_labels,
        allowed_label_families,
        max_variants_per_peptide,
        out_dir,
    )


COMMANDS = (
    fasta_provenance_command,
    fasta_decoy_command,
    target_decoy_validate_command,
    digest_command,
    theoretical_digest_command,
)
