# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Targeted matrix and assay QC CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.targeted_matrix_qc import (
    run_targeted_assay_qc_command,
    run_targeted_carryover_review_command,
    run_targeted_target_matrix_command,
    run_transition_qc_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("transition-qc")
@click.argument(
    "transition_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--weak-detection-fraction-threshold",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--weak-relative-share-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sample-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--weak-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def transition_qc_command(
    transition_table: Path,
    weak_detection_fraction_threshold: float,
    weak_relative_share_threshold: float,
    summary_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review transition-level quantitative evidence from one canonical table."""
    return run_transition_qc_command(
        transition_table,
        weak_detection_fraction_threshold,
        weak_relative_share_threshold,
        summary_tsv_out,
        transition_tsv_out,
        sample_tsv_out,
        weak_tsv_out,
        out_path,
    )


@click.command("targeted-target-matrix")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--observation-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sample-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--flagged-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--retained-transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--excluded-transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--missingness-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_target_matrix_command(
    input_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    observation_tsv_out: Path | None,
    target_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    flagged_tsv_out: Path | None,
    retained_transition_tsv_out: Path | None,
    excluded_transition_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import targeted assay results and build a precursor-target matrix review."""
    return run_targeted_target_matrix_command(
        input_path,
        source_kind,
        summary_tsv_out,
        observation_tsv_out,
        target_tsv_out,
        sample_tsv_out,
        flagged_tsv_out,
        retained_transition_tsv_out,
        excluded_transition_tsv_out,
        missingness_tsv_out,
        out_path,
    )


@click.command("targeted-assay-qc")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-qc-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--coelution-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--transition-coelution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--transition-qc-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--fragment-ratio-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--retention-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--replicate-cv-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--unreliable-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_assay_qc_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    target_qc_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    coelution_tsv_out: Path | None,
    transition_coelution_tsv_out: Path | None,
    transition_qc_tsv_out: Path | None,
    fragment_ratio_tsv_out: Path | None,
    retention_tsv_out: Path | None,
    replicate_cv_tsv_out: Path | None,
    unreliable_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import targeted assay results and build assay-QC review ledgers."""
    return run_targeted_assay_qc_command(
        input_path,
        design_path,
        source_kind,
        summary_tsv_out,
        target_qc_tsv_out,
        transition_tsv_out,
        coelution_tsv_out,
        transition_coelution_tsv_out,
        transition_qc_tsv_out,
        fragment_ratio_tsv_out,
        retention_tsv_out,
        replicate_cv_tsv_out,
        unreliable_tsv_out,
        out_path,
    )


@click.command("targeted-carryover-review")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--candidate-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_carryover_review_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review ordered targeted runs for carryover candidates."""
    return run_targeted_carryover_review_command(
        input_path,
        design_path,
        source_kind,
        summary_tsv_out,
        candidate_tsv_out,
        out_path,
    )


COMMANDS = (
    transition_qc_command,
    targeted_target_matrix_command,
    targeted_assay_qc_command,
    targeted_carryover_review_command,
)
