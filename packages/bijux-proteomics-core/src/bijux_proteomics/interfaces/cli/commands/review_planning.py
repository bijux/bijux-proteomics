# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Belief audit and validation planning CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.review_planning import (
    run_belief_audit_command,
    run_targeted_panel_builder_command,
    run_validation_experiment_planner_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("belief-audit")
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
    "--validation-evidence-card-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--validation-evidence-warning-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--run-qc-assessment-tsv",
    "run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--belief-audit-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def belief_audit_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    validation_evidence_card_tsv: Path | None,
    validation_evidence_warning_tsv: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    summary_tsv_out: Path | None,
    belief_audit_tsv_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    """Audit why governed conclusions were retained, weakened, and falsifiable."""
    return run_belief_audit_command(
        biological_report_dir,
        ptm_report_dir,
        validation_evidence_card_tsv,
        validation_evidence_warning_tsv,
        run_qc_assessment_tsv_paths,
        summary_tsv_out,
        belief_audit_tsv_out,
        html_out,
        out_path,
    )


@click.command("targeted-panel-builder")
@click.argument(
    "biomarker_candidate_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "selected_peptide_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "assay_interference_assay_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "assay_interference_transition_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--spectral-library",
    "spectral_library_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--assay-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--panel-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--omitted-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_panel_builder_command(
    biomarker_candidate_tsv: Path,
    selected_peptide_tsv: Path,
    assay_interference_assay_tsv: Path,
    assay_interference_transition_tsv: Path,
    spectral_library_path: Path | None,
    summary_tsv_out: Path | None,
    assay_tsv_out: Path | None,
    panel_tsv_out: Path | None,
    omitted_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a targeted transition-list panel from ranked candidates and retained assays."""
    return run_targeted_panel_builder_command(
        biomarker_candidate_tsv,
        selected_peptide_tsv,
        assay_interference_assay_tsv,
        assay_interference_transition_tsv,
        spectral_library_path,
        summary_tsv_out,
        assay_tsv_out,
        panel_tsv_out,
        omitted_tsv_out,
        out_path,
    )


@click.command("validation-experiment-planner")
@click.argument(
    "biomarker_candidate_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "selected_peptide_tsv",
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
    "--power-variance-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--proposed-samples-per-group",
    type=int,
    default=6,
    show_default=True,
)
@click.option("--fdr-target", type=float, default=0.05, show_default=True)
@click.option("--target-power", type=float, default=0.8, show_default=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--plan-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--warning-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def validation_experiment_planner_command(
    biomarker_candidate_tsv: Path,
    selected_peptide_tsv: Path,
    panel_assay_tsv: Path,
    panel_omitted_tsv: Path | None,
    power_variance_tsv: Path | None,
    proposed_samples_per_group: int,
    fdr_target: float,
    target_power: float,
    summary_tsv_out: Path | None,
    plan_tsv_out: Path | None,
    warning_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Plan targeted validation experiments from biomarker, peptide, and panel evidence."""
    return run_validation_experiment_planner_command(
        biomarker_candidate_tsv,
        selected_peptide_tsv,
        panel_assay_tsv,
        panel_omitted_tsv,
        power_variance_tsv,
        proposed_samples_per_group,
        fdr_target,
        target_power,
        summary_tsv_out,
        plan_tsv_out,
        warning_tsv_out,
        out_path,
    )


COMMANDS = (
    belief_audit_command,
    targeted_panel_builder_command,
    validation_experiment_planner_command,
)
