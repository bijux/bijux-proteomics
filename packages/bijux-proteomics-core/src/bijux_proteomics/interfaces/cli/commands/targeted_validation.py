# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Targeted validation and biomarker stability CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.targeted_validation import (
    run_biomarker_panel_redundancy_analysis_command,
    run_biomarker_stability_analysis_command,
    run_targeted_result_validator_command,
    run_validation_evidence_cards_command,
)
from bijux_proteomics.interfaces.support.multiplex_targeted.targeted import (
    TargetedResultSourceKind,
)


@click.command("targeted-result-validator")
@click.argument(
    "biomarker_candidate_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "panel_assay_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "targeted_result_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--case-condition", required=True)
@click.option("--control-condition", required=True)
@click.option(
    "--minimum-reliable-replicates-per-condition",
    type=int,
    default=2,
    show_default=True,
)
@click.option(
    "--minimum-absolute-validation-log2-effect",
    type=float,
    default=0.4,
    show_default=True,
)
@click.option(
    "--flat-validation-log2-threshold",
    type=float,
    default=0.2,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--confirmed-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--contradicted-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--inconclusive-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--evidence-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_result_validator_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    targeted_result_tsv: Path,
    design_path: Path,
    source_kind: str,
    case_condition: str,
    control_condition: str,
    minimum_reliable_replicates_per_condition: int,
    minimum_absolute_validation_log2_effect: float,
    flat_validation_log2_threshold: float,
    summary_tsv_out: Path | None,
    confirmed_tsv_out: Path | None,
    contradicted_tsv_out: Path | None,
    inconclusive_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate targeted PRM/SRM results back against discovery biomarker claims."""
    return run_targeted_result_validator_command(
        biomarker_candidate_tsv,
        panel_assay_tsv,
        targeted_result_tsv,
        design_path,
        source_kind,
        case_condition,
        control_condition,
        minimum_reliable_replicates_per_condition,
        minimum_absolute_validation_log2_effect,
        flat_validation_log2_threshold,
        summary_tsv_out,
        confirmed_tsv_out,
        contradicted_tsv_out,
        inconclusive_tsv_out,
        evidence_tsv_out,
        out_path,
    )


@click.command("biomarker-stability-analysis")
@click.argument(
    "biomarker_candidate_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "panel_assay_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "targeted_result_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-timepoint-field", default="timepoint", show_default=True)
@click.option("--design-sample-type-field", default="sample_type", show_default=True)
@click.option(
    "--minimum-reliable-samples-per-group",
    type=int,
    default=2,
    show_default=True,
)
@click.option(
    "--minimum-reliable-sample-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--subgroup-median-delta-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--batch-residual-delta-threshold",
    type=float,
    default=0.75,
    show_default=True,
)
@click.option(
    "--assay-disagreement-delta-threshold",
    type=float,
    default=0.75,
    show_default=True,
)
@click.option(
    "--downgrade-below-score",
    type=float,
    default=0.75,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--stability-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--subgroup-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--adjusted-candidate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def biomarker_stability_analysis_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    targeted_result_tsv: Path,
    design_path: Path,
    source_kind: str,
    design_batch_field: str,
    design_timepoint_field: str,
    design_sample_type_field: str,
    minimum_reliable_samples_per_group: int,
    minimum_reliable_sample_fraction: float,
    subgroup_median_delta_threshold: float,
    batch_residual_delta_threshold: float,
    assay_disagreement_delta_threshold: float,
    downgrade_below_score: float,
    summary_tsv_out: Path | None,
    stability_tsv_out: Path | None,
    subgroup_tsv_out: Path | None,
    adjusted_candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Assess biomarker stability across targeted-study subgroups."""
    return run_biomarker_stability_analysis_command(
        biomarker_candidate_tsv,
        panel_assay_tsv,
        targeted_result_tsv,
        design_path,
        source_kind,
        design_batch_field,
        design_timepoint_field,
        design_sample_type_field,
        minimum_reliable_samples_per_group,
        minimum_reliable_sample_fraction,
        subgroup_median_delta_threshold,
        batch_residual_delta_threshold,
        assay_disagreement_delta_threshold,
        downgrade_below_score,
        summary_tsv_out,
        stability_tsv_out,
        subgroup_tsv_out,
        adjusted_candidate_tsv_out,
        out_path,
    )


@click.command("biomarker-panel-redundancy-analysis")
@click.argument(
    "biomarker_candidate_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "panel_assay_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "targeted_result_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option(
    "--minimum-shared-samples",
    type=int,
    default=4,
    show_default=True,
)
@click.option(
    "--correlation-threshold",
    type=float,
    default=0.95,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--cluster-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--reduced-candidate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--dropped-candidate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def biomarker_panel_redundancy_analysis_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    targeted_result_tsv: Path,
    design_path: Path,
    source_kind: str,
    minimum_shared_samples: int,
    correlation_threshold: float,
    summary_tsv_out: Path | None,
    cluster_tsv_out: Path | None,
    reduced_candidate_tsv_out: Path | None,
    dropped_candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Detect redundant targeted biomarker candidates and keep explicit representatives."""
    return run_biomarker_panel_redundancy_analysis_command(
        biomarker_candidate_tsv,
        panel_assay_tsv,
        targeted_result_tsv,
        design_path,
        source_kind,
        minimum_shared_samples,
        correlation_threshold,
        summary_tsv_out,
        cluster_tsv_out,
        reduced_candidate_tsv_out,
        dropped_candidate_tsv_out,
        out_path,
    )


@click.command("validation-evidence-cards")
@click.argument(
    "biomarker_candidate_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "panel_assay_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--panel-omitted-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--confirmed-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--contradicted-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--inconclusive-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--validation-evidence-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--stability-candidate-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--redundancy-candidate-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--card-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--assay-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--warning-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def validation_evidence_cards_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    panel_omitted_tsv: Path | None,
    confirmed_tsv: Path | None,
    contradicted_tsv: Path | None,
    inconclusive_tsv: Path | None,
    validation_evidence_tsv: Path | None,
    stability_candidate_tsv: Path | None,
    redundancy_candidate_tsv: Path | None,
    summary_tsv_out: Path | None,
    card_tsv_out: Path | None,
    assay_tsv_out: Path | None,
    warning_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Assemble candidate-level validation evidence cards from governed TSV outputs."""
    return run_validation_evidence_cards_command(
        biomarker_candidate_tsv,
        panel_assay_tsv,
        panel_omitted_tsv,
        confirmed_tsv,
        contradicted_tsv,
        inconclusive_tsv,
        validation_evidence_tsv,
        stability_candidate_tsv,
        redundancy_candidate_tsv,
        summary_tsv_out,
        card_tsv_out,
        assay_tsv_out,
        warning_tsv_out,
        out_path,
    )


COMMANDS = (
    targeted_result_validator_command,
    biomarker_stability_analysis_command,
    biomarker_panel_redundancy_analysis_command,
    validation_evidence_cards_command,
)
