# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PSM and evidence review CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.identification_evidence import (
    run_cross_run_reproducibility_command,
    run_peptide_evidence_command,
    run_protein_evidence_command,
    run_psm_inspect_command,
    run_psm_map_command,
)
from bijux_proteomics.interfaces.support.identification import ScoreOrientation
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _score_orientation_choice,
)


@click.command("psm-map")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mapping",
    "mapping_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--normalized-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def psm_map_command(
    input_tsv: Path,
    mapping_path: Path,
    normalized_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map a lab-local PSM table through an explicit YAML or JSON column map."""
    return run_psm_map_command(
        input_tsv, mapping_path, normalized_tsv_out, rejected_tsv_out, out_path
    )


@click.command("psm-inspect")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--protease", default="trypsin", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--score-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--q-value-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peptide-length-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missed-cleavage-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def psm_inspect_command(
    input_tsv: Path,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    protease: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    summary_tsv_out: Path | None,
    score_distribution_tsv_out: Path | None,
    q_value_distribution_tsv_out: Path | None,
    charge_distribution_tsv_out: Path | None,
    peptide_length_distribution_tsv_out: Path | None,
    missed_cleavage_distribution_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Inspect a generic PSM TSV and emit normalized summaries."""
    return run_psm_inspect_command(
        input_tsv,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        q_value_column,
        pep_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        protease,
        decoy_prefix,
        decoy_suffix,
        jsonl_out,
        tsv_out,
        provenance_out,
        summary_tsv_out,
        score_distribution_tsv_out,
        q_value_distribution_tsv_out,
        charge_distribution_tsv_out,
        peptide_length_distribution_tsv_out,
        missed_cleavage_distribution_tsv_out,
        out_path,
    )


@click.command("peptide-evidence")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--strong-q-value", type=float, default=0.01, show_default=True)
@click.option("--reproducible-spectrum-count", type=int, default=2, show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def peptide_evidence_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    strong_q_value: float,
    reproducible_spectrum_count: int,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review classified peptide evidence with strong, moderate, shared, and weak states."""
    return run_peptide_evidence_command(
        input_tsv,
        threshold,
        score_orientation,
        strong_q_value,
        reproducible_spectrum_count,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        q_value_column,
        pep_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        summary_tsv_out,
        entries_tsv_out,
        out_path,
    )


@click.command("protein-evidence")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--high-q-value", type=float, default=0.01, show_default=True)
@click.option("--moderate-q-value", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option(
    "--design-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--exploratory-protein", multiple=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_evidence_command(
    input_tsv: Path,
    high_q_value: float,
    moderate_q_value: float,
    score_orientation: str,
    design_tsv: Path | None,
    exploratory_protein: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review final protein evidence tiers with explicit downgrade reasons."""
    return run_protein_evidence_command(
        input_tsv,
        high_q_value,
        moderate_q_value,
        score_orientation,
        design_tsv,
        exploratory_protein,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        q_value_column,
        pep_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        summary_tsv_out,
        entries_tsv_out,
        out_path,
    )


@click.command("cross-run-reproducibility")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-type",
    type=click.Choice(("peptide", "protein"), case_sensitive=False),
    default="peptide",
    show_default=True,
)
@click.option(
    "--design-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--exploratory-entity", multiple=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default="run_id", show_default=True)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def cross_run_reproducibility_command(
    input_tsv: Path,
    entity_type: str,
    design_tsv: Path,
    exploratory_entity: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score peptide or protein evidence by cross-run detection consistency."""
    return run_cross_run_reproducibility_command(
        input_tsv,
        entity_type,
        design_tsv,
        exploratory_entity,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        q_value_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        summary_tsv_out,
        entries_tsv_out,
        out_path,
    )


COMMANDS = (
    psm_map_command,
    psm_inspect_command,
    peptide_evidence_command,
    protein_evidence_command,
    cross_run_reproducibility_command,
)
