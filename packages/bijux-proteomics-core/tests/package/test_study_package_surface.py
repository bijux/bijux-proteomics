# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import study
from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


def test_study_package_exports_lab_qc_status_surface() -> None:
    observed_mz = calculate_peptide_mz("ACDEFGK", charge=2)
    run_report = study.build_lcms_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="study-package:scan-001",
                precursor_mz=observed_mz,
                precursor_charge=2,
                retention_time_seconds=120.0,
                peaks=(
                    SpectrumPeak(mz=observed_mz - 10.0, intensity=800.0),
                    SpectrumPeak(mz=observed_mz, intensity=3200.0),
                ),
            ),
        ),
        (
            PsmRecord(
                spectrum_id="study-package:scan-001",
                peptide="ACDEFGK",
                canonical_peptide="ACDEFGK",
                charge=2,
                score=120.0,
                q_value=0.01,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        design_entry=ExperimentalDesignEntry(
            sample_id="STUDY1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="study-package.mgf",
            identifications_file="study-package.tsv",
            metadata={"enrichment_marker_refs": "P11111"},
        ),
        protein_sequences={"P11111": "KACDEFGKRAA"},
        run_id="study-package-run",
    )

    assessment = study.build_run_qc_assessment(
        run_report,
        policy=study.default_qc_threshold_policy().model_copy(update={"rules": ()}),
    )

    assert study.QcStatus.PASS.value == "pass"
    assert assessment.qc_status is study.QcStatus.PASS
    assert assessment.status_reasons == ()
    assert "qc_status" in study.render_qc_assessment_tsv(assessment).splitlines()[0]


def test_study_package_exports_experiment_design_surface() -> None:
    design = study.build_experiment_design(
        (
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="run-001",
                batch="B1",
                instrument="Orbitrap-1",
                metadata={
                    "timepoint": "T0",
                    "species": "human",
                    "tissue_or_cell_type": "hepatocyte",
                    "perturbation": "vehicle",
                },
            ),
        )
    )

    assert hasattr(study, "ExperimentDesign")
    assert hasattr(study, "build_experiment_design")
    assert design.summary.sample_count == 1
    assert design.summary.run_count == 1
    assert design.timepoints == ("T0",)


def test_study_package_exports_design_validity_surface() -> None:
    design = study.build_experiment_design(
        (
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="run-001",
            ),
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="run-002",
            ),
        )
    )

    report = study.build_experiment_design_validity_report(
        design,
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(study, "build_experiment_design_validity_report")
    assert hasattr(study, "require_valid_experiment_design_for_differential_analysis")
    assert report.summary.sample_identity_conflict_count == 1
    assert "conflicting_sample_identity" in study.render_experiment_design_validity_tsv(
        report
    )


def test_study_package_exports_design_classification_surface() -> None:
    design = study.build_experiment_design(
        (
            ExperimentalDesignEntry(
                sample_id="control_r1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control_r1.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treat_r1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treat_r1.raw",
            ),
        )
    )

    report = study.build_experiment_design_classification_report(design)

    assert hasattr(study, "build_experiment_design_classification_report")
    assert hasattr(study, "require_matching_experiment_design_analysis_family")
    assert report.primary_design_type.value == "two_group"
    assert "pairwise_differential" in study.render_experiment_design_classification_tsv(
        report
    )


def test_study_package_exports_experiment_feasibility_surface() -> None:
    design = study.build_experiment_design(
        (
            ExperimentalDesignEntry(
                sample_id="control_1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control_1.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="control_2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="control_2.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treated_1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treated_1.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treated_2",
                condition="treatment",
                replicate=2,
                fraction=1,
                spectra_file="treated_2.raw",
            ),
        )
    )

    report = study.build_experiment_feasibility_report(design)

    assert hasattr(study, "build_experiment_feasibility_report")
    assert hasattr(study, "require_feasible_experiment_design_for_analysis")
    assert report.summary.valid_contrast_count == 1
    assert report.model_support[0].analysis_family.value == "pairwise_differential"
    assert "analysis_family" in study.render_experiment_feasibility_model_support_tsv(
        report
    )


def test_study_package_exports_sample_run_identity_surface() -> None:
    report = study.build_sample_run_identity_report(
        (
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="run-001",
                technical_replicate_id="tech-1",
            ),
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="run-002",
                technical_replicate_id="tech-2",
            ),
        ),
        policy=study.SampleRunAnalysisPolicy.SEPARATE_TECHNICAL_RUNS,
    )

    assert hasattr(study, "build_sample_run_identity_report")
    assert hasattr(study, "resolve_sample_run_analysis_entries")
    assert report.summary.analysis_sample_count == 2
    assert report.run_assignments[0].biological_sample_id == "S1"


def test_study_package_exports_replicate_structure_surface() -> None:
    report = study.build_replicate_structure_report(
        (
            ExperimentalDesignEntry(
                sample_id="subject-1_t0",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="subject-1_t0_run-1.mzml",
                pair_id="subject-1",
                technical_replicate_id="tech-1",
                metadata={"timepoint": "T0"},
            ),
            ExperimentalDesignEntry(
                sample_id="subject-1_t1",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="subject-1_t1_run-1.mzml",
                pair_id="subject-1",
                technical_replicate_id="tech-2",
                metadata={"timepoint": "T1"},
            ),
            ExperimentalDesignEntry(
                sample_id="treated-1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treated-1_run-1.mzml",
            ),
            ExperimentalDesignEntry(
                sample_id="treated-2",
                condition="treatment",
                replicate=2,
                fraction=1,
                spectra_file="treated-2_run-1.mzml",
            ),
        )
    )

    assert hasattr(study, "build_replicate_structure_report")
    assert hasattr(study, "count_effective_statistical_units_by_condition")
    assert report.summary.repeated_measure_subject_count == 1
    assert study.count_effective_statistical_units_by_condition(report.experiment_design) == {
        "control": 1,
        "treatment": 2,
    }
    assert "effective_statistical_unit_count" in study.render_replicate_structure_tsv(
        report
    )


def test_study_package_exports_sample_sheet_repair_suggestion_surface() -> None:
    report = study.build_sample_sheet_repair_suggestion_report(
        (
            ExperimentalDesignEntry(
                sample_id="control_1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control_1.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treated_1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="missing_run.raw",
            ),
        ),
        observed_sample_ids=("control_1", "treated_1", "treated_2"),
        observed_run_ids=("control_1.raw", "treated_1.raw", "treated_2.raw"),
    )

    assert hasattr(study, "build_sample_sheet_repair_suggestion_report")
    assert hasattr(study, "render_sample_sheet_repair_suggestions_tsv")
    assert report.summary.missing_metadata_sample_count == 1
    assert report.summary.metadata_run_mismatch_count == 1
    assert "suggested_fields_json" in study.render_sample_sheet_repair_suggestions_tsv(
        report
    )
