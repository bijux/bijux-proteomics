# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from bijux_proteomics import domain, study
from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    MissingnessConditionSummaryEntry,
    MissingnessConditionSummaryReport,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.power_estimation import (
    PowerEffectSizeGridEntry,
    PowerEstimationPolicy,
    PowerEstimationReport,
    PowerEstimationSummary,
)
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


def test_study_package_exports_shared_experiment_confidence_tier() -> None:
    assert study.ExperimentConfidenceTier is domain.ConfidenceTier
    assert study.ExperimentConfidenceTier.HIGH_CONFIDENCE.value == "high"


def test_study_package_exports_carryover_detection_surface() -> None:
    rows = study.detect_carryover(
        (
            study.CarryoverRunOrderEntry(run_id="source_high.raw", run_order=1),
            study.CarryoverRunOrderEntry(run_id="blank_after_source.raw", run_order=2),
        ),
        (
            study.CarryoverIntensityEntry(
                run_id="source_high.raw",
                entity_id="CARRYPEP/2",
                intensity=200000.0,
            ),
            study.CarryoverIntensityEntry(
                run_id="blank_after_source.raw",
                entity_id="CARRYPEP/2",
                intensity=4000.0,
            ),
        ),
    )
    rendered = study.render_carryover_detection_tsv(rows)

    assert hasattr(study, "detect_carryover")
    assert hasattr(study, "render_carryover_detection_tsv")
    assert rows[0].carryover_score == 0.9333
    assert "affected_intensity" in rendered


def test_study_package_exports_lc_drift_detection_surface() -> None:
    rows = study.detect_lc_drift(
        (
            study.LcDriftRunQcEntry(
                run_id="run-01",
                run_order=1,
                median_rt=900.0,
                tic=1_000_000.0,
                ms2_count=5000,
                id_count=1200,
                median_peak_width=12.0,
            ),
            study.LcDriftRunQcEntry(
                run_id="run-02",
                run_order=2,
                median_rt=920.0,
                tic=920_000.0,
                ms2_count=4975,
                id_count=1180,
                median_peak_width=12.0,
            ),
            study.LcDriftRunQcEntry(
                run_id="run-03",
                run_order=3,
                median_rt=940.0,
                tic=840_000.0,
                ms2_count=4950,
                id_count=1160,
                median_peak_width=12.0,
            ),
            study.LcDriftRunQcEntry(
                run_id="run-04",
                run_order=4,
                median_rt=960.0,
                tic=760_000.0,
                ms2_count=4925,
                id_count=1140,
                median_peak_width=12.0,
            ),
        )
    )
    rendered = study.render_lc_drift_tsv(rows)

    assert hasattr(study, "detect_lc_drift")
    assert hasattr(study, "render_lc_drift_tsv")
    assert rows[0].affected_qc_dimension.value == "median_rt"
    assert rows[-1].affected_qc_dimension.value == "tic"
    assert "affected_qc_dimension" in rendered


def test_study_package_exports_batch_condition_confounding_surface() -> None:
    report = study.detect_batch_condition_confounding(
        (
            ExperimentalDesignEntry(
                sample_id="case-1",
                condition="case",
                replicate=1,
                fraction=1,
                spectra_file="case-1.mzml",
                batch="batch-a",
            ),
            ExperimentalDesignEntry(
                sample_id="case-2",
                condition="case",
                replicate=2,
                fraction=1,
                spectra_file="case-2.mzml",
                batch="batch-a",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="ctrl-1.mzml",
                batch="batch-b",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="ctrl-2.mzml",
                batch="batch-b",
            ),
        )
    )
    rendered = study.render_batch_condition_confounding_tsv(report)

    assert hasattr(study, "detect_batch_condition_confounding")
    assert hasattr(study, "render_batch_condition_confounding_tsv")
    assert report.is_confounded is True
    assert report.blocked_contrasts == ("case_vs_control",)
    assert "confounded_terms" in rendered


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


def test_study_package_exports_lab_protocol_context_surface(tmp_path: Path) -> None:
    protocol_path = tmp_path / "protocol.tsv"
    protocol_path.write_text(
        "\n".join(
            (
                "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                "prot-001\ttrypsin\tdia\tlabel_free\tnone\tnone\tnone\tOrbitrap Exploris",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = study.parse_lab_protocol_context_table(protocol_path)
    entry = study.require_single_lab_protocol_context(report)
    profile = study.build_lab_protocol_interpretation_profile(entry)

    assert hasattr(study, "parse_lab_protocol_context_table")
    assert hasattr(study, "build_lab_protocol_interpretation_profile")
    assert hasattr(study, "build_protocol_aware_qc_threshold_policy")
    assert profile.interpretation_focus == "dia_discovery"
    assert study.render_lab_protocol_context_tsv(report).splitlines()[1].startswith(
        "prot-001\ttrypsin\tdia"
    )


def test_study_package_exports_protocol_consistency_surface() -> None:
    report = study.build_protocol_consistency_report(
        study.LabProtocolContextEntry(
            protocol_id="tmt-1",
            digestion_enzyme=study.DigestionEnzyme.OTHER,
            acquisition_type=study.AcquisitionType.DDA,
            labeling_method=study.LabelingMethod.TMT,
            enrichment_type=study.EnrichmentType.NONE,
            fractionation_mode=study.FractionationMode.NONE,
            depletion_mode=study.DepletionMode.NONE,
            instrument_platform="Orbitrap Eclipse",
            metadata={},
        ),
        reporter_import_report=SimpleNamespace(
            accepted_rows=(
                SimpleNamespace(
                    channel_intensities=(
                        SimpleNamespace(multiplex_channel="126", intensity=1200.0),
                        SimpleNamespace(multiplex_channel="127N", intensity=900.0),
                    )
                ),
            ),
        ),
    )

    assert hasattr(study, "build_protocol_consistency_report")
    assert hasattr(study, "render_protocol_consistency_tsv")
    assert hasattr(study, "require_protocol_consistency_without_blockers")
    assert report.summary.status is study.ProtocolConsistencyStatus.PASS
    assert study.render_protocol_consistency_tsv(report).splitlines()[0].startswith(
        "protocol_id\taxis\tcode\tseverity"
    )


def test_study_package_exports_experiment_confidence_surface() -> None:
    report = study.build_experiment_confidence_report(
        study.build_experiment_design(
            (
                ExperimentalDesignEntry(
                    sample_id="C1",
                    condition="control",
                    replicate=1,
                    fraction=1,
                    spectra_file="c1.raw",
                ),
                ExperimentalDesignEntry(
                    sample_id="T1",
                    condition="treatment",
                    replicate=1,
                    fraction=1,
                    spectra_file="t1.raw",
                ),
            )
        ),
        missingness_condition_summary_report=MissingnessConditionSummaryReport(
            entity_level=QuantEntityLevel.PROTEIN,
            entries=(
                MissingnessConditionSummaryEntry(
                    condition="control",
                    sample_ids=("C1",),
                    observed_value_count=10,
                    zero_value_count=0,
                    not_observed_value_count=0,
                    filtered_value_count=0,
                    missing_fraction=0.0,
                    condition_specific_absence_entity_ids=(),
                ),
                MissingnessConditionSummaryEntry(
                    condition="treatment",
                    sample_ids=("T1",),
                    observed_value_count=8,
                    zero_value_count=0,
                    not_observed_value_count=2,
                    filtered_value_count=0,
                    missing_fraction=0.2,
                    condition_specific_absence_entity_ids=("P22222",),
                ),
            ),
        ),
        power_estimation_report=PowerEstimationReport(
            summary=PowerEstimationSummary(
                entity_level=QuantEntityLevel.PROTEIN,
                measure_kind=QuantMeasureKind.INTENSITY,
                aggregation_method=QuantRollupMethod.SUM,
                normalization_method="none",
                sample_count=2,
                evaluated_entity_count=20,
                fdr_target=0.05,
                target_power=0.8,
                weaker_power_with_fewer_replicates=True,
            ),
            policy=PowerEstimationPolicy(candidate_replicates_per_condition=(2, 3)),
            variance_entries=(),
            effect_size_grid=(
                PowerEffectSizeGridEntry(
                    replicates_per_condition=2,
                    evaluable_entity_count=20,
                    median_effective_replicates_per_condition=1.8,
                    median_detectable_log2_fold_change=1.2,
                    p75_detectable_log2_fold_change=1.5,
                ),
            ),
            note="package surface proof",
        ),
    )

    assert hasattr(study, "build_experiment_confidence_report")
    assert hasattr(study, "render_experiment_confidence_summary_tsv")
    assert hasattr(study, "render_experiment_confidence_component_tsv")
    assert report.summary.component_count == 7
    assert "overall_score" in study.render_experiment_confidence_summary_tsv(report)


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
