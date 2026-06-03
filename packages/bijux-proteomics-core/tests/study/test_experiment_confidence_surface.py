# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
    build_missingness_condition_summary_report,
    build_power_estimation_report,
)
from bijux_proteomics.study import (
    AcquisitionType,
    DigestionEnzyme,
    EnrichmentType,
    ExperimentConfidenceComponentKind,
    FractionationMode,
    LabelingMethod,
    LabProtocolContextEntry,
    build_experiment_confidence_report,
    build_experiment_design,
    build_lcms_run_qc_report,
    build_protocol_consistency_report,
    build_run_qc_assessment,
    default_qc_threshold_policy,
    render_experiment_confidence_component_tsv,
    render_experiment_confidence_summary_tsv,
)
from bijux_proteomics.study.lab_protocol_context import DepletionMode


def _design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="C1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="C2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="T1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="T2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.raw",
        ),
    )


def _quant_table() -> LabelFreeQuantTable:
    values = (
        QuantValue(
            sample_id="C1",
            entity_id="P11111",
            abundance=1200.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=2,
        ),
        QuantValue(
            sample_id="C2",
            entity_id="P11111",
            abundance=1100.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=2,
        ),
        QuantValue(
            sample_id="T1",
            entity_id="P11111",
            abundance=3000.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=2,
        ),
        QuantValue(
            sample_id="T2",
            entity_id="P11111",
            abundance=3200.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=2,
        ),
        QuantValue(
            sample_id="C1",
            entity_id="P22222",
            abundance=800.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=1,
        ),
        QuantValue(
            sample_id="C2",
            entity_id="P22222",
            abundance=780.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=1,
        ),
        QuantValue(
            sample_id="T1",
            entity_id="P22222",
            abundance=None,
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
            source_feature_count=0,
        ),
        QuantValue(
            sample_id="T2",
            entity_id="P22222",
            abundance=None,
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
            source_feature_count=0,
        ),
        QuantValue(
            sample_id="C1",
            entity_id="P33333",
            abundance=500.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=1,
        ),
        QuantValue(
            sample_id="C2",
            entity_id="P33333",
            abundance=520.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=1,
        ),
        QuantValue(
            sample_id="T1",
            entity_id="P33333",
            abundance=490.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=1,
        ),
        QuantValue(
            sample_id="T2",
            entity_id="P33333",
            abundance=510.0,
            missing_value_kind=MissingValueKind.OBSERVED,
            source_feature_count=1,
        ),
    )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "T1", "T2"),
        entity_ids=("P11111", "P22222", "P33333"),
        values=values,
        entity_protein_refs={
            "P11111": ("P11111",),
            "P22222": ("P22222",),
            "P33333": ("P33333",),
        },
        entity_member_peptides={
            "P11111": ("PEPTIDEK",),
            "P22222": ("CNTAMK",),
            "P33333": ("ANOTHERK",),
        },
    )


def _run_qc_report():
    peptide_a = "PEPTIDEK"
    peptide_b = "CNTAMK"
    spectra = (
        SpectrumModel(
            spectrum_id="scan-001",
            precursor_mz=calculate_peptide_mz(peptide_a, charge=2),
            precursor_charge=2,
            retention_time_seconds=120.0,
            peaks=(SpectrumPeak(mz=100.0, intensity=1000.0),),
        ),
        SpectrumModel(
            spectrum_id="scan-002",
            precursor_mz=calculate_peptide_mz(peptide_b, charge=2),
            precursor_charge=2,
            retention_time_seconds=180.0,
            peaks=(SpectrumPeak(mz=120.0, intensity=1100.0),),
        ),
        SpectrumModel(
            spectrum_id="scan-003",
            precursor_mz=400.2,
            precursor_charge=2,
            retention_time_seconds=240.0,
            peaks=(SpectrumPeak(mz=140.0, intensity=900.0),),
        ),
        SpectrumModel(
            spectrum_id="scan-004",
            precursor_mz=500.2,
            precursor_charge=2,
            retention_time_seconds=300.0,
            peaks=(SpectrumPeak(mz=160.0, intensity=950.0),),
        ),
    )
    psms = (
        PsmRecord(
            spectrum_id="scan-001",
            peptide=peptide_a,
            canonical_peptide=peptide_a,
            charge=2,
            score=120.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-002",
            peptide=peptide_b,
            canonical_peptide=peptide_b,
            charge=2,
            score=95.0,
            protein_refs=("CON__KERATIN1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )
    return build_lcms_run_qc_report(
        spectra=spectra,
        psm_records=psms,
        protein_sequences={
            "P11111": "MPEPTIDEKAA",
            "CON__KERATIN1": "MCNTAMKAA",
        },
        run_id="run-001",
    )


def _protocol() -> LabProtocolContextEntry:
    return LabProtocolContextEntry(
        protocol_id="prot-001",
        digestion_enzyme=DigestionEnzyme.TRYPSIN,
        acquisition_type=AcquisitionType.DDA,
        labeling_method=LabelingMethod.LABEL_FREE,
        enrichment_type=EnrichmentType.NONE,
        fractionation_mode=FractionationMode.NONE,
        depletion_mode=DepletionMode.NONE,
        instrument_platform="Orbitrap Eclipse",
        metadata={},
    )


def test_experiment_confidence_report_scores_decomposed_components() -> None:
    design = build_experiment_design(_design_entries())
    quant_table = _quant_table()
    run_qc_report = _run_qc_report()
    protocol_consistency_report = build_protocol_consistency_report(
        _protocol(),
        run_qc_report=run_qc_report,
    )

    report = build_experiment_confidence_report(
        design,
        missingness_condition_summary_report=build_missingness_condition_summary_report(
            quant_table,
            design_entries=design.entries,
        ),
        power_estimation_report=build_power_estimation_report(
            quant_table,
            design.entries,
        ),
        run_qc_reports=(run_qc_report,),
        run_qc_assessments=(
            build_run_qc_assessment(
                run_qc_report,
                policy=default_qc_threshold_policy(),
            ),
        ),
        protocol_consistency_report=protocol_consistency_report,
        warning_card_count=2,
        protein_card_count=4,
    )

    components = {component.component: component for component in report.components}

    assert report.summary.component_count == 7
    assert report.summary.overall_score < 1.0
    assert report.summary.low_confidence_component_count >= 1
    assert (
        ExperimentConfidenceComponentKind.MISSINGNESS in components
        and "condition_specific_absence"
        in components[ExperimentConfidenceComponentKind.MISSINGNESS].reason_codes
    )
    assert (
        ExperimentConfidenceComponentKind.CONTAMINATION in components
        and "severe_contamination"
        in components[ExperimentConfidenceComponentKind.CONTAMINATION].reason_codes
    )
    assert ExperimentConfidenceComponentKind.RUN_QC in components and {
        "caution_run_qc",
        "failed_run_qc",
    }.intersection(components[ExperimentConfidenceComponentKind.RUN_QC].reason_codes)
    assert (
        ExperimentConfidenceComponentKind.EVIDENCE_CONSISTENCY in components
        and "frequent_result_card_warnings"
        in components[
            ExperimentConfidenceComponentKind.EVIDENCE_CONSISTENCY
        ].reason_codes
    )
    assert "overall_score" in render_experiment_confidence_summary_tsv(report)
    assert (
        "component\tscore\ttier\treason_codes\tmessage"
        in render_experiment_confidence_component_tsv(report)
    )


def test_experiment_confidence_report_marks_unavailable_inputs_explicitly() -> None:
    design = build_experiment_design(_design_entries())
    quant_table = _quant_table()

    report = build_experiment_confidence_report(
        design,
        missingness_condition_summary_report=build_missingness_condition_summary_report(
            quant_table,
            design_entries=design.entries,
        ),
        power_estimation_report=build_power_estimation_report(
            quant_table,
            design.entries,
        ),
    )

    components = {component.component: component for component in report.components}

    assert (
        "run_qc_not_available"
        in components[ExperimentConfidenceComponentKind.RUN_QC].reason_codes
    )
    assert (
        "contamination_not_available"
        in components[ExperimentConfidenceComponentKind.CONTAMINATION].reason_codes
    )
    assert (
        "protocol_consistency_not_available"
        in components[
            ExperimentConfidenceComponentKind.EVIDENCE_CONSISTENCY
        ].reason_codes
    )
