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
