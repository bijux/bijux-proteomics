# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Belief audit and validation planning CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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
    'Audit why governed conclusions were retained, weakened, and falsifiable.'
    return run_belief_audit_command(biological_report_dir, ptm_report_dir, validation_evidence_card_tsv, validation_evidence_warning_tsv, run_qc_assessment_tsv_paths, summary_tsv_out, belief_audit_tsv_out, html_out, out_path)

def run_belief_audit_command(
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
    if (
        biological_report_dir is None
        and ptm_report_dir is None
        and validation_evidence_card_tsv is None
        and not run_qc_assessment_tsv_paths
    ):
        raise click.ClickException(
            "at least one governed biological report, PTM report, validation evidence card, or QC assessment input must be provided"
        )

    try:
        report = build_belief_audit_report_from_artifacts(
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            validation_evidence_card_tsv=validation_evidence_card_tsv,
            validation_evidence_warning_tsv=validation_evidence_warning_tsv,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        )
        html = render_belief_audit_html(report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_belief_audit_summary_tsv(report))
    if belief_audit_tsv_out is not None:
        _write_text_output(belief_audit_tsv_out, render_belief_audit_tsv(report))
    if html_out is not None:
        _write_text_output(html_out, html)

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "validation_evidence_card_tsv": (
            None
            if validation_evidence_card_tsv is None
            else str(validation_evidence_card_tsv)
        ),
        "validation_evidence_warning_tsv": (
            None
            if validation_evidence_warning_tsv is None
            else str(validation_evidence_warning_tsv)
        ),
        "run_qc_assessment_tsv_paths": [str(path) for path in run_qc_assessment_tsv_paths],
        "report": report.to_dict(),
        "html": html,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "belief_audit_tsv": (
                None
                if belief_audit_tsv_out is None
                else str(belief_audit_tsv_out)
            ),
            "html": None if html_out is None else str(html_out),
        },
    }
    _emit_json(payload, out_path=out_path)

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
    'Build a targeted transition-list panel from ranked candidates and retained assays.'
    return run_targeted_panel_builder_command(biomarker_candidate_tsv, selected_peptide_tsv, assay_interference_assay_tsv, assay_interference_transition_tsv, spectral_library_path, summary_tsv_out, assay_tsv_out, panel_tsv_out, omitted_tsv_out, out_path)

def run_targeted_panel_builder_command(
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
    biomarker_candidates = _load_biomarker_candidate_inputs(biomarker_candidate_tsv)
    selected_peptides = _load_targeted_panel_selected_peptides(selected_peptide_tsv)
    assay_inputs = _load_targeted_panel_assay_inputs(assay_interference_assay_tsv)
    transition_inputs = _load_targeted_panel_transition_inputs(
        assay_interference_transition_tsv
    )
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = ()
    spectral_library_summary_payload: dict[str, object] | None = None
    if spectral_library_path is not None:
        import_report = import_spectral_library(spectral_library_path)
        spectral_library_entries = import_report.entries
        spectral_library_summary_payload = build_spectral_library_summary(
            import_report
        ).to_dict()

    try:
        report = build_targeted_panel_design_report(
            biomarker_candidates=biomarker_candidates,
            selected_peptides=selected_peptides,
            assay_entries=assay_inputs,
            transition_entries=transition_inputs,
            spectral_library_entries=spectral_library_entries,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_targeted_panel_design_summary_tsv(report))
    if assay_tsv_out is not None:
        _write_text_output(assay_tsv_out, render_targeted_panel_design_assay_tsv(report))
    if panel_tsv_out is not None:
        _write_text_output(panel_tsv_out, render_targeted_panel_design_panel_tsv(report))
    if omitted_tsv_out is not None:
        _write_text_output(
            omitted_tsv_out,
            render_targeted_panel_design_omitted_candidate_tsv(report),
        )

    payload = {
        "biomarker_candidate_tsv": str(biomarker_candidate_tsv),
        "selected_peptide_tsv": str(selected_peptide_tsv),
        "assay_interference_assay_tsv": str(assay_interference_assay_tsv),
        "assay_interference_transition_tsv": str(assay_interference_transition_tsv),
        "spectral_library": spectral_library_summary_payload,
        "summary": report.summary.to_dict(),
        "assay_entries": [entry.to_dict() for entry in report.assay_entries],
        "panel_entries": [entry.to_dict() for entry in report.panel_entries],
        "omitted_candidates": [entry.to_dict() for entry in report.omitted_candidates],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "assay_tsv": None if assay_tsv_out is None else str(assay_tsv_out),
            "panel_tsv": None if panel_tsv_out is None else str(panel_tsv_out),
            "omitted_tsv": None if omitted_tsv_out is None else str(omitted_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

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
    'Plan targeted validation experiments from biomarker, peptide, and panel evidence.'
    return run_validation_experiment_planner_command(biomarker_candidate_tsv, selected_peptide_tsv, panel_assay_tsv, panel_omitted_tsv, power_variance_tsv, proposed_samples_per_group, fdr_target, target_power, summary_tsv_out, plan_tsv_out, warning_tsv_out, out_path)

def run_validation_experiment_planner_command(
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
    biomarker_candidates = _load_validation_planning_biomarker_candidates(
        biomarker_candidate_tsv
    )
    selected_peptides = _load_validation_planning_selected_peptides(selected_peptide_tsv)
    panel_assays = _load_validation_planning_panel_assays(panel_assay_tsv)
    omitted_candidates = (
        ()
        if panel_omitted_tsv is None
        else _load_validation_planning_omitted_candidates(panel_omitted_tsv)
    )
    pilot_variance_entries = (
        ()
        if power_variance_tsv is None
        else _load_validation_planning_pilot_variance(power_variance_tsv)
    )

    try:
        report = build_validation_experiment_planning_report(
            biomarker_candidates=biomarker_candidates,
            selected_peptides=selected_peptides,
            panel_assays=panel_assays,
            pilot_variance_entries=pilot_variance_entries,
            omitted_candidates=omitted_candidates,
            policy=ValidationExperimentPlanningPolicy(
                proposed_samples_per_group=proposed_samples_per_group,
                fdr_target=fdr_target,
                target_power=target_power,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_validation_experiment_planning_summary_tsv(report),
        )
    if plan_tsv_out is not None:
        _write_text_output(
            plan_tsv_out,
            render_validation_experiment_planning_plan_tsv(report),
        )
    if warning_tsv_out is not None:
        _write_text_output(
            warning_tsv_out,
            render_validation_experiment_planning_warning_tsv(report),
        )

    payload = {
        "biomarker_candidate_tsv": str(biomarker_candidate_tsv),
        "selected_peptide_tsv": str(selected_peptide_tsv),
        "panel_assay_tsv": str(panel_assay_tsv),
        "panel_omitted_tsv": None if panel_omitted_tsv is None else str(panel_omitted_tsv),
        "power_variance_tsv": None if power_variance_tsv is None else str(power_variance_tsv),
        "policy": report.policy.to_dict(),
        "summary": report.summary.to_dict(),
        "plan_entries": [entry.to_dict() for entry in report.plan_entries],
        "warnings": [entry.to_dict() for entry in report.warnings],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "plan_tsv": None if plan_tsv_out is None else str(plan_tsv_out),
            "warning_tsv": None if warning_tsv_out is None else str(warning_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    belief_audit_command,
    targeted_panel_builder_command,
    validation_experiment_planner_command,
)
