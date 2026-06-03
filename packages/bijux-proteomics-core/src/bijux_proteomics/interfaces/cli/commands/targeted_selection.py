# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Targeted peptide, transition, and biomarker selection CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.targeted_selection import (
    run_biomarker_candidate_ranking_command,
    run_targeted_assay_interference_command,
    run_targeted_peptide_selection_command,
    run_targeted_transition_selection_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("targeted-peptide-selection")
@click.argument(
    "protein_card_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "peptide_evidence_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--protease", default="trypsin", show_default=True)
@click.option("--missed-cleavages", default=0, type=int, show_default=True)
@click.option("--top-peptides-per-target", default=3, type=int, show_default=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--selected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_peptide_selection_command(
    protein_card_tsv: Path,
    peptide_evidence_tsv: Path,
    input_fasta: Path,
    protease: str,
    missed_cleavages: int,
    top_peptides_per_target: int,
    summary_tsv_out: Path | None,
    selected_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Select targeted assay peptides from discovery protein and peptide evidence."""
    return run_targeted_peptide_selection_command(
        protein_card_tsv,
        peptide_evidence_tsv,
        input_fasta,
        protease,
        missed_cleavages,
        top_peptides_per_target,
        summary_tsv_out,
        selected_tsv_out,
        rejected_tsv_out,
        out_path,
    )


@click.command("targeted-transition-selection")
@click.argument(
    "selected_peptide_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--spectral-library",
    "spectral_library_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--spectral-library-format",
    type=click.Choice([entry.value for entry in SpectralLibraryFormat]),
    default=None,
)
@click.option("--default-precursor-charge", default=2, type=int, show_default=True)
@click.option(
    "--fragment-charge",
    "fragment_charges",
    type=int,
    multiple=True,
    default=(1, 2),
    show_default=True,
)
@click.option(
    "--min-transitions-per-peptide",
    default=3,
    type=int,
    show_default=True,
)
@click.option(
    "--max-transitions-per-peptide",
    default=5,
    type=int,
    show_default=True,
)
@click.option("--min-fragment-mz", default=300.0, type=float, show_default=True)
@click.option("--max-fragment-mz", default=1500.0, type=float, show_default=True)
@click.option("--precursor-exclusion-da", default=8.0, type=float, show_default=True)
@click.option(
    "--library-match-tolerance-da",
    default=0.02,
    type=float,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--selected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_transition_selection_command(
    selected_peptide_tsv: Path,
    spectral_library_path: Path | None,
    spectral_library_format: str | None,
    default_precursor_charge: int,
    fragment_charges: tuple[int, ...],
    min_transitions_per_peptide: int,
    max_transitions_per_peptide: int,
    min_fragment_mz: float,
    max_fragment_mz: float,
    precursor_exclusion_da: float,
    library_match_tolerance_da: float,
    summary_tsv_out: Path | None,
    selected_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Select chemistry-driven fragment transitions for targeted assay peptides."""
    return run_targeted_transition_selection_command(
        selected_peptide_tsv,
        spectral_library_path,
        spectral_library_format,
        default_precursor_charge,
        fragment_charges,
        min_transitions_per_peptide,
        max_transitions_per_peptide,
        min_fragment_mz,
        max_fragment_mz,
        precursor_exclusion_da,
        library_match_tolerance_da,
        summary_tsv_out,
        selected_tsv_out,
        rejected_tsv_out,
        out_path,
    )


@click.command("targeted-assay-interference")
@click.argument(
    "selected_peptide_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "selected_transition_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "input_fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--spectral-library",
    "spectral_library_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--spectral-library-format",
    type=click.Choice([entry.value for entry in SpectralLibraryFormat]),
    default=None,
)
@click.option("--protease", default="trypsin", show_default=True)
@click.option("--missed-cleavages", default=0, type=int, show_default=True)
@click.option("--precursor-tolerance-da", default=1.0, type=float, show_default=True)
@click.option("--fragment-tolerance-da", default=0.02, type=float, show_default=True)
@click.option(
    "--coelution-rt-window-minutes",
    default=0.5,
    type=float,
    show_default=True,
)
@click.option(
    "--min-export-transitions",
    default=3,
    type=int,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--assay-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--transition-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--panel-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_assay_interference_command(
    selected_peptide_tsv: Path,
    selected_transition_tsv: Path,
    input_fasta: Path,
    spectral_library_path: Path | None,
    spectral_library_format: str | None,
    protease: str,
    missed_cleavages: int,
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
    min_export_transitions: int,
    summary_tsv_out: Path | None,
    assay_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    panel_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score targeted assay interference before panel export."""
    return run_targeted_assay_interference_command(
        selected_peptide_tsv,
        selected_transition_tsv,
        input_fasta,
        spectral_library_path,
        spectral_library_format,
        protease,
        missed_cleavages,
        precursor_tolerance_da,
        fragment_tolerance_da,
        coelution_rt_window_minutes,
        min_export_transitions,
        summary_tsv_out,
        assay_tsv_out,
        transition_tsv_out,
        panel_tsv_out,
        out_path,
    )


@click.command("biomarker-candidate-ranking")
@click.option(
    "--biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--selected-peptide-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--assay-interference-assay-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--candidate-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def biomarker_candidate_ranking_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    selected_peptide_tsv: Path | None,
    assay_interference_assay_tsv: Path | None,
    summary_tsv_out: Path | None,
    candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Rank protein and PTM validation candidates from governed report artifacts."""
    return run_biomarker_candidate_ranking_command(
        biological_report_dir,
        ptm_report_dir,
        selected_peptide_tsv,
        assay_interference_assay_tsv,
        summary_tsv_out,
        candidate_tsv_out,
        out_path,
    )


COMMANDS = (
    targeted_peptide_selection_command,
    targeted_transition_selection_command,
    targeted_assay_interference_command,
    biomarker_candidate_ranking_command,
)
