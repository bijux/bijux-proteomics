# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, cast

from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.quantification import (
    NormalizationMethod,
    QuantEntityLevel,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.study.qc import (
    QcAssessmentSeverity,
    QcStatus,
    QcDigestionSpecificity,
    QcEvidenceInputFile,
    QcThresholdPolicy,
    build_batch_qc_assessment,
    build_instrument_batch_qc_report,
    build_lcms_run_qc_report,
    build_performance_snapshot,
    build_qc_evidence_manifest,
    build_qc_publication_decision,
    build_qc_run_bundle_summary,
    build_run_qc_assessment,
    build_study_qc_summary,
    default_qc_threshold_policy,
    render_qc_assessment_html,
    render_qc_assessment_tsv,
)

PROTEIN_SEQUENCES = {
    "P11111": "KACDEFGKRAA",
    "CON__KERATIN": "KMSSQQLLLLKA",
    "SPECIES_HUMAN": "KLMNOPQRKAA".replace("O", "A"),
    "SPECIES_MOUSE": "KQRSTAAAKAA",
    "SEX_FEMALE": "KFGHIKLMKAA",
    "SEX_MALE": "KLMNPKQRKAA",
    "TRYPSIN_LAB": "KTRYPSINKAA",
}


def _qc_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "qc" / name


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "quant" / name


def _design_entries() -> dict[str, ExperimentalDesignEntry]:
    report = parse_experimental_design_table(_qc_fixture("batch.design.tsv"))
    return {entry.sample_id: entry for entry in report.accepted_entries}


def _strict_qc_policy() -> QcThresholdPolicy:
    return default_qc_threshold_policy().model_copy(
        update={
            "rules": tuple(
                rule.model_copy(update={"lower_fail": 0.5})
                if rule.metric_key == "identification_rate"
                else rule
                for rule in default_qc_threshold_policy().rules
            )
        }
    )


class _JsonPayload(Protocol):
    def model_dump(self, *, mode: str) -> dict[str, Any]: ...


def _normalized_document_json(payload: _JsonPayload) -> str:
    data = payload.model_dump(mode="json")
    if "document_schema" in data:
        data["document_schema"]["created_at"] = "2000-01-01T00:00:00Z"
        data["document_schema"]["updated_at"] = "2000-01-01T00:00:00Z"

    def _scrub_policy_hashes(value: object) -> object:
        if isinstance(value, dict):
            scrubbed: dict[str, object] = {}
            for key, item in value.items():
                if key in {"policy_sha256", "rule_sha256"}:
                    scrubbed[key] = "<policy_sha256>"
                else:
                    scrubbed[key] = _scrub_policy_hashes(item)
            return scrubbed
        if isinstance(value, list):
            return [_scrub_policy_hashes(item) for item in value]
        return value

    data = cast(dict[str, Any], _scrub_policy_hashes(data))
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _spectrum_for_peptide(
    spectrum_id: str,
    peptide: str,
    *,
    charge: int,
    retention_time_seconds: float,
    ppm_error: float,
) -> SpectrumModel:
    theoretical_mz = calculate_peptide_mz(peptide, charge=charge)
    observed_mz = theoretical_mz * (1.0 + (ppm_error / 1_000_000.0))
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=observed_mz,
        precursor_charge=charge,
        retention_time_seconds=retention_time_seconds,
        peaks=(
            SpectrumPeak(mz=max(observed_mz - 20.0, 50.0), intensity=1200.0),
            SpectrumPeak(mz=observed_mz, intensity=4200.0),
            SpectrumPeak(mz=observed_mz + 15.0, intensity=800.0),
        ),
    )


def _unidentified_spectrum(
    spectrum_id: str,
    *,
    charge: int,
    retention_time_seconds: float,
) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=500.0,
        precursor_charge=charge,
        retention_time_seconds=retention_time_seconds,
        peaks=(
            SpectrumPeak(mz=200.0, intensity=1000.0),
            SpectrumPeak(mz=500.0, intensity=3000.0),
        ),
    )


def _psm(
    spectrum_id: str,
    peptide: str,
    *,
    charge: int,
    score: float,
    protein_refs: tuple[str, ...],
) -> PsmRecord:
    return PsmRecord(
        spectrum_id=spectrum_id,
        peptide=peptide,
        canonical_peptide=peptide,
        charge=charge,
        score=score,
        q_value=0.01,
        protein_refs=protein_refs,
        target_decoy_label=TargetDecoyLabel.TARGET,
    )


def _run_a_spectra() -> tuple[SpectrumModel, ...]:
    return (
        _spectrum_for_peptide(
            "run-a:scan-001",
            "ACDEFGK",
            charge=2,
            retention_time_seconds=100.0,
            ppm_error=1.0,
        ),
        _spectrum_for_peptide(
            "run-a:scan-002",
            "ACDEFGKR",
            charge=3,
            retention_time_seconds=160.0,
            ppm_error=-1.5,
        ),
        _spectrum_for_peptide(
            "run-a:scan-003",
            "CDEFGK",
            charge=2,
            retention_time_seconds=220.0,
            ppm_error=2.0,
        ),
        _spectrum_for_peptide(
            "run-a:scan-004",
            "DEFG",
            charge=1,
            retention_time_seconds=280.0,
            ppm_error=-2.5,
        ),
        _spectrum_for_peptide(
            "run-a:scan-005",
            "MSSQQLLLLK",
            charge=2,
            retention_time_seconds=340.0,
            ppm_error=1.2,
        ),
        _unidentified_spectrum(
            "run-a:scan-006", charge=2, retention_time_seconds=400.0
        ),
    )


def _run_a_psms() -> tuple[PsmRecord, ...]:
    return (
        _psm(
            "run-a:scan-001", "ACDEFGK", charge=2, score=120.0, protein_refs=("P11111",)
        ),
        _psm(
            "run-a:scan-002",
            "ACDEFGKR",
            charge=3,
            score=118.0,
            protein_refs=("P11111",),
        ),
        _psm(
            "run-a:scan-003", "CDEFGK", charge=2, score=110.0, protein_refs=("P11111",)
        ),
        _psm("run-a:scan-004", "DEFG", charge=1, score=90.0, protein_refs=("P11111",)),
        _psm(
            "run-a:scan-005",
            "MSSQQLLLLK",
            charge=2,
            score=87.0,
            protein_refs=("CON__KERATIN",),
        ),
    )


def _run_b_spectra() -> tuple[SpectrumModel, ...]:
    return (
        _spectrum_for_peptide(
            "run-b:scan-001",
            "ACDEFGK",
            charge=2,
            retention_time_seconds=105.0,
            ppm_error=0.8,
        ),
        _spectrum_for_peptide(
            "run-b:scan-002",
            "ACDEFGKR",
            charge=3,
            retention_time_seconds=165.0,
            ppm_error=-1.1,
        ),
        _spectrum_for_peptide(
            "run-b:scan-003",
            "CDEFGK",
            charge=2,
            retention_time_seconds=230.0,
            ppm_error=1.7,
        ),
        _spectrum_for_peptide(
            "run-b:scan-004",
            "MSSQQLLLLK",
            charge=2,
            retention_time_seconds=295.0,
            ppm_error=1.4,
        ),
        _unidentified_spectrum(
            "run-b:scan-005", charge=2, retention_time_seconds=360.0
        ),
        _unidentified_spectrum(
            "run-b:scan-006", charge=3, retention_time_seconds=420.0
        ),
    )


def _run_b_psms() -> tuple[PsmRecord, ...]:
    return (
        _psm(
            "run-b:scan-001", "ACDEFGK", charge=2, score=122.0, protein_refs=("P11111",)
        ),
        _psm(
            "run-b:scan-002",
            "ACDEFGKR",
            charge=3,
            score=117.0,
            protein_refs=("P11111",),
        ),
        _psm(
            "run-b:scan-003", "CDEFGK", charge=2, score=111.0, protein_refs=("P11111",)
        ),
        _psm(
            "run-b:scan-004",
            "MSSQQLLLLK",
            charge=2,
            score=88.0,
            protein_refs=("CON__KERATIN",),
        ),
    )


def _run_c_spectra() -> tuple[SpectrumModel, ...]:
    return (
        _spectrum_for_peptide(
            "run-c:scan-001",
            "ACDEFGK",
            charge=2,
            retention_time_seconds=110.0,
            ppm_error=12.0,
        ),
        _spectrum_for_peptide(
            "run-c:scan-002",
            "MSSQQLLLLK",
            charge=2,
            retention_time_seconds=175.0,
            ppm_error=-14.0,
        ),
        _unidentified_spectrum(
            "run-c:scan-003", charge=2, retention_time_seconds=240.0
        ),
        _unidentified_spectrum(
            "run-c:scan-004", charge=2, retention_time_seconds=305.0
        ),
        _unidentified_spectrum(
            "run-c:scan-005", charge=3, retention_time_seconds=370.0
        ),
        _unidentified_spectrum(
            "run-c:scan-006", charge=2, retention_time_seconds=435.0
        ),
    )


def _run_c_psms() -> tuple[PsmRecord, ...]:
    return (
        _psm(
            "run-c:scan-001", "ACDEFGK", charge=2, score=101.0, protein_refs=("P11111",)
        ),
        _psm(
            "run-c:scan-002",
            "MSSQQLLLLK",
            charge=2,
            score=74.0,
            protein_refs=("CON__KERATIN",),
        ),
    )


def test_build_lcms_run_qc_report_captures_run_level_metrics() -> None:
    design_entry = _design_entries()["S1"]
    quant_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    source_quant_table = normalize_label_free_table(
        build_label_free_intensity_table(
            quant_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    quant_table = source_quant_table.model_copy(
        update={
            "sample_ids": tuple(
                "S1" if sample_id == "C1" else sample_id
                for sample_id in source_quant_table.sample_ids
            ),
            "values": tuple(
                value.model_copy(
                    update={
                        "sample_id": "S1"
                        if value.sample_id == "C1"
                        else value.sample_id
                    }
                )
                for value in source_quant_table.values
            ),
            "normalization_factors": {
                ("S1" if sample_id == "C1" else sample_id): factor
                for sample_id, factor in source_quant_table.normalization_factors.items()
            },
        }
    )
    report = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entry,
        protein_sequences=PROTEIN_SEQUENCES,
        quant_table=quant_table,
    )

    specificity = {entry.specificity: entry for entry in report.digestion_specificity}

    assert report.run_id == "run-a"
    assert report.sample_id == "S1"
    assert report.batch == "B1"
    assert report.instrument_summary.instrument == "Orbitrap-A"
    assert report.instrument_summary.spectra_with_precursor_charge == 6
    assert report.identification_summary.identified_spectrum_count == 5
    assert report.spectrum_count == 6
    assert report.identified_spectrum_count == 5
    assert round(report.identification_rate, 3) == 0.833
    assert report.mass_error.matched_psm_count == 5
    assert report.retention_time.span_seconds == 300.0
    assert report.retention_time.identified_span_seconds == 240.0
    assert report.missed_cleavage_count == 1
    assert report.missed_cleavage_rate == 0.2
    assert report.contaminant_summary.contaminant_psm_count == 1
    assert report.contaminant_summary.contaminant_psm_fraction == 0.2
    assert report.contaminant_summary.contaminant_peptide_count == 1
    assert report.contaminant_summary.contaminant_protein_count == 1
    assert report.contaminant_summary.contaminant_intensity == 0.0
    assert report.contaminant_summary.total_psm_intensity == 0.0
    assert report.contaminant_summary.contaminant_intensity_fraction == 0.0
    assert report.quant_summary is not None
    assert report.quant_summary.sample_id == "S1"
    assert report.quant_summary.entity_level.value == "protein"
    assert report.quant_summary.total_entity_count >= 5
    assert specificity[QcDigestionSpecificity.ENZYMATIC].count == 3
    assert specificity[QcDigestionSpecificity.SEMI_SPECIFIC].count == 1
    assert specificity[QcDigestionSpecificity.NON_SPECIFIC].count == 1


def test_build_lcms_run_qc_report_tracks_charge_and_contaminant_distribution() -> None:
    report = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        protein_sequences=PROTEIN_SEQUENCES,
    )

    spectrum_charges = {
        entry.charge_label: entry.count for entry in report.spectrum_charge_distribution
    }
    identified_charges = {
        entry.charge_label: entry.count
        for entry in report.identified_charge_distribution
    }

    assert spectrum_charges == {"1": 1, "2": 4, "3": 1}
    assert identified_charges == {"1": 1, "2": 3, "3": 1}
    assert report.contaminant_summary.contaminant_peptide_count == 1
    assert report.contaminant_summary.contaminant_protein_count == 1
    assert report.contaminant_summary.contaminant_protein_counts == {"CON__KERATIN": 1}
    assert report.mass_error.median_abs_ppm is not None
    assert report.mass_error.max_abs_ppm is not None
    assert any(
        entry.category.value == "contamination" for entry in report.run_anomalies
    )


def test_build_lcms_run_qc_report_warns_for_contaminant_heavy_intensity_burden() -> None:
    design_entry = _design_entries()["S1"]
    spectra = (
        _spectrum_for_peptide(
            "run-a:scan-101",
            "MSSQQLLLLK",
            charge=2,
            retention_time_seconds=120.0,
            ppm_error=1.1,
        ),
        _spectrum_for_peptide(
            "run-a:scan-102",
            "ACDEFGK",
            charge=2,
            retention_time_seconds=180.0,
            ppm_error=-0.8,
        ),
    )
    psms = (
        _psm(
            "run-a:scan-101",
            "MSSQQLLLLK",
            charge=2,
            score=95.0,
            protein_refs=("CON__KERATIN",),
        ).model_copy(update={"intensity": 900.0}),
        _psm(
            "run-a:scan-102",
            "ACDEFGK",
            charge=2,
            score=110.0,
            protein_refs=("P11111",),
        ).model_copy(update={"intensity": 100.0}),
    )

    report = build_lcms_run_qc_report(
        spectra,
        psms,
        design_entry=design_entry,
        protein_sequences=PROTEIN_SEQUENCES,
    )

    assert report.contaminant_summary.contaminant_psm_fraction == 0.5
    assert report.contaminant_summary.contaminant_intensity == 900.0
    assert report.contaminant_summary.total_psm_intensity == 1000.0
    assert report.contaminant_summary.contaminant_intensity_fraction == 0.9
    assert any(
        entry.code == "elevated_contaminant_fraction"
        for entry in report.run_anomalies
    )


def test_build_lcms_run_qc_report_emits_typed_run_anomalies() -> None:
    design_entry = _design_entries()["S3"]
    report = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entry,
        protein_sequences=PROTEIN_SEQUENCES,
    )

    categories = {entry.category.value for entry in report.run_anomalies}
    assert "identification" in categories
    assert "quantification" in categories


def test_build_instrument_batch_qc_report_flags_outlier_run() -> None:
    design_entries = _design_entries()
    run_a = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entries["S1"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_b = build_lcms_run_qc_report(
        _run_b_spectra(),
        _run_b_psms(),
        design_entry=design_entries["S2"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_c = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entries["S3"],
        protein_sequences=PROTEIN_SEQUENCES,
    )

    batch_report = build_instrument_batch_qc_report((run_a, run_b, run_c))
    outlier = next(entry for entry in batch_report.runs if entry.run_id == "run-c")

    assert batch_report.batch_id == "B1"
    assert batch_report.instrument == "Orbitrap-A"
    assert batch_report.run_count == 3
    assert batch_report.outlier_run_ids == ("run-c",)
    assert "low_identification_rate" in outlier.outlier_reasons
    assert "high_mass_error" in outlier.outlier_reasons


def test_build_study_qc_summary_compares_conditions_and_batches() -> None:
    design_entries = _design_entries()
    run_a = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entries["S1"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_b = build_lcms_run_qc_report(
        _run_b_spectra(),
        _run_b_psms(),
        design_entry=design_entries["S2"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_c = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entries["S3"],
        protein_sequences=PROTEIN_SEQUENCES,
    )

    summary = build_study_qc_summary((run_a, run_b, run_c), study_id="study-01")
    control = next(
        entry for entry in summary.condition_summaries if entry.condition == "control"
    )
    batch = next(entry for entry in summary.batch_summaries if entry.batch_id == "B1")

    assert summary.study_id == "study-01"
    assert summary.run_count == 3
    assert control.run_ids == ("run-a", "run-b")
    assert batch.outlier_run_ids == ("run-c",)
    assert summary.overall_identification_rate_span > 0.0


def test_qc_threshold_policy_assesses_run_and_batch_reports() -> None:
    design_entries = _design_entries()
    run_a = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entries["S1"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_c = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entries["S3"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    policy = _strict_qc_policy()

    run_assessment = build_run_qc_assessment(run_c, policy=policy)
    batch_report = build_instrument_batch_qc_report((run_a, run_c))
    batch_assessment = build_batch_qc_assessment(batch_report, policy=policy)

    assert run_assessment.blocked is True
    assert run_assessment.overall_severity is QcAssessmentSeverity.FAILED
    assert run_assessment.threshold_profile.enforced_rules
    assert run_assessment.threshold_profile.advisory_rules
    assert "identification_rate" in run_assessment.enforced_failure_metric_keys
    identification_metric = next(
        entry
        for entry in run_assessment.metric_assessments
        if entry.metric_key == "identification_rate"
    )
    assert run_assessment.policy_sha256
    assert identification_metric.provenance is not None
    assert identification_metric.provenance.triggered_threshold == "lower_fail"
    assert (
        identification_metric.provenance.policy_sha256 == run_assessment.policy_sha256
    )
    assert any(
        entry.metric_key == "identification_rate" and entry.enforced_violation
        for entry in run_assessment.metric_assessments
    )
    assert batch_assessment.overall_severity in {
        QcAssessmentSeverity.WARNING,
        QcAssessmentSeverity.FAILED,
    }
    assert batch_assessment.threshold_profile.advisory_rules
    assert any(
        entry.metric_key == "outlier_run_count"
        for entry in batch_assessment.metric_assessments
    )


def test_qc_renderers_match_regression_fixtures() -> None:
    design_entries = _design_entries()
    run_a = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entries["S1"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_c = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entries["S3"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    policy = _strict_qc_policy()
    run_assessment = build_run_qc_assessment(run_c, policy=policy)
    batch_report = build_instrument_batch_qc_report((run_a, run_c))
    batch_assessment = build_batch_qc_assessment(batch_report, policy=policy)

    tsv = render_qc_assessment_tsv(run_assessment, batch_assessment=batch_assessment)
    html = render_qc_assessment_html(
        run_c,
        run_assessment,
        batch_report=batch_report,
        batch_assessment=batch_assessment,
    )

    assert tsv == _qc_fixture("qc_assessment_expected.tsv").read_text(encoding="utf-8")
    assert html == _qc_fixture("qc_assessment_expected.html").read_text(
        encoding="utf-8"
    )


def test_qc_assessment_marks_unknown_metric_reasons_explicitly() -> None:
    report = build_lcms_run_qc_report(
        (
            _unidentified_spectrum(
                "unknown:scan-001", charge=2, retention_time_seconds=120.0
            ),
        ),
        (),
        run_id="unknown-run",
        protein_sequences=PROTEIN_SEQUENCES,
    )
    assessment = build_run_qc_assessment(report, policy=default_qc_threshold_policy())
    mass_error_metric = next(
        entry
        for entry in assessment.metric_assessments
        if entry.metric_key == "median_abs_mass_error_ppm"
    )

    assert mass_error_metric.severity is QcAssessmentSeverity.NOT_ASSESSED
    assert mass_error_metric.unknown_state_reason is not None
    assert mass_error_metric.unknown_state_reason.value == "no_matched_psms"


def test_qc_run_assessment_emits_pass_caution_fail_statuses_with_reason_codes() -> None:
    base_policy = default_qc_threshold_policy()
    empty_rule_policy = base_policy.model_copy(update={"rules": ()})

    pass_design = ExperimentalDesignEntry(
        sample_id="PASS1",
        condition="control",
        replicate=1,
        fraction=1,
        spectra_file="pass.mgf",
        identifications_file="pass.tsv",
        metadata={
            "expected_species_marker_refs": "SPECIES_HUMAN",
            "expected_sex_marker_refs": "SEX_FEMALE",
            "enrichment_marker_refs": "P11111",
        },
    )
    pass_report = build_lcms_run_qc_report(
        (
            _spectrum_for_peptide(
                "pass:scan-001",
                "ACDEFGK",
                charge=2,
                retention_time_seconds=100.0,
                ppm_error=0.8,
            ),
            _spectrum_for_peptide(
                "pass:scan-002",
                "FGHIK",
                charge=2,
                retention_time_seconds=170.0,
                ppm_error=-0.9,
            ),
            _spectrum_for_peptide(
                "pass:scan-003",
                "LMNAPQR",
                charge=2,
                retention_time_seconds=240.0,
                ppm_error=1.1,
            ),
        ),
        (
            _psm("pass:scan-001", "ACDEFGK", charge=2, score=120.0, protein_refs=("P11111",)),
            _psm(
                "pass:scan-002",
                "FGHIK",
                charge=2,
                score=118.0,
                protein_refs=("SEX_FEMALE",),
            ),
            _psm(
                "pass:scan-003",
                "LMNAPQR",
                charge=2,
                score=119.0,
                protein_refs=("SPECIES_HUMAN",),
            ),
        ),
        design_entry=pass_design,
        protein_sequences=PROTEIN_SEQUENCES,
        run_id="pass-run",
    )
    pass_assessment = build_run_qc_assessment(pass_report, policy=empty_rule_policy)
    assert pass_assessment.sample_id == "PASS1"
    assert pass_assessment.qc_status is QcStatus.PASSED
    assert pass_assessment.status_reasons == ()

    caution_design = ExperimentalDesignEntry(
        sample_id="CAUTION1",
        condition="control",
        replicate=1,
        fraction=1,
        spectra_file="caution.mgf",
        identifications_file="caution.tsv",
        metadata={
            "carryover_marker_refs": "TRYPSIN_LAB",
            "enrichment_marker_refs": "SPECIES_HUMAN",
        },
    )
    caution_report = build_lcms_run_qc_report(
        (
            _spectrum_for_peptide(
                "caution:scan-001",
                "ACDEFGK",
                charge=2,
                retention_time_seconds=110.0,
                ppm_error=0.7,
            ),
            _spectrum_for_peptide(
                "caution:scan-002",
                "YPSINK",
                charge=2,
                retention_time_seconds=180.0,
                ppm_error=-0.6,
            ),
        ),
        (
            _psm(
                "caution:scan-001",
                "ACDEFGK",
                charge=2,
                score=120.0,
                protein_refs=("P11111",),
            ),
            _psm(
                "caution:scan-002",
                "YPSINK",
                charge=2,
                score=117.0,
                protein_refs=("TRYPSIN_LAB",),
            ),
        ),
        design_entry=caution_design,
        protein_sequences=PROTEIN_SEQUENCES,
        run_id="caution-run",
    )
    caution_assessment = build_run_qc_assessment(
        caution_report, policy=empty_rule_policy
    )
    assert caution_assessment.qc_status is QcStatus.CAUTION
    assert {reason.code for reason in caution_assessment.status_reasons} == {
        "carryover_suspected",
        "enrichment_inefficiency",
    }

    fail_design = ExperimentalDesignEntry(
        sample_id="FAIL1",
        condition="treatment",
        replicate=1,
        fraction=1,
        spectra_file="fail.mgf",
        identifications_file="fail.tsv",
        metadata={
            "expected_species_marker_refs": "SPECIES_HUMAN",
            "forbidden_species_marker_refs": "SPECIES_MOUSE",
            "expected_sex_marker_refs": "SEX_FEMALE",
            "forbidden_sex_marker_refs": "SEX_MALE",
        },
    )
    fail_report = build_lcms_run_qc_report(
        (
            _spectrum_for_peptide(
                "fail:scan-001",
                "STAAAK",
                charge=2,
                retention_time_seconds=120.0,
                ppm_error=0.9,
            ),
            _spectrum_for_peptide(
                "fail:scan-002",
                "LMNPK",
                charge=2,
                retention_time_seconds=190.0,
                ppm_error=-0.5,
            ),
        ),
        (
            _psm(
                "fail:scan-001",
                "STAAAK",
                charge=2,
                score=116.0,
                protein_refs=("SPECIES_MOUSE",),
            ),
            _psm(
                "fail:scan-002",
                "LMNPK",
                charge=2,
                score=115.0,
                protein_refs=("SEX_MALE",),
            ),
        ),
        design_entry=fail_design,
        protein_sequences=PROTEIN_SEQUENCES,
        run_id="fail-run",
    )
    fail_assessment = build_run_qc_assessment(fail_report, policy=empty_rule_policy)
    assert fail_assessment.qc_status is QcStatus.FAIL
    assert {reason.code for reason in fail_assessment.status_reasons} == {
        "sample_swap_suspected",
        "sex_marker_mismatch",
        "species_marker_mismatch",
    }
    assert all(reason.message for reason in fail_assessment.status_reasons)


def test_qc_edge_case_fixtures_cover_sparse_runs_and_single_run_batches() -> None:
    run_report = build_lcms_run_qc_report(
        (
            _unidentified_spectrum(
                "edge:scan-001", charge=2, retention_time_seconds=90.0
            ),
            _unidentified_spectrum(
                "edge:scan-002", charge=2, retention_time_seconds=95.0
            ),
        ),
        (),
        run_id="edge-run",
        protein_sequences=PROTEIN_SEQUENCES,
    )
    assessment = build_run_qc_assessment(
        run_report, policy=default_qc_threshold_policy()
    )
    batch_report = build_instrument_batch_qc_report(
        (run_report,),
        batch_id="edge-batch",
        instrument="edge-instrument",
    )
    performance = build_performance_snapshot(
        "edge-run",
        operations={
            "parse_spectra": (0.0, 2),
            "build_qc": (0.01, 2),
        },
    )

    assert _normalized_document_json(assessment) == _qc_fixture(
        "edge_run_assessment_expected.json"
    ).read_text(encoding="utf-8")
    assert _normalized_document_json(batch_report) == _qc_fixture(
        "edge_batch_report_expected.json"
    ).read_text(encoding="utf-8")
    assert _normalized_document_json(performance) == _qc_fixture(
        "edge_performance_snapshot_expected.json"
    ).read_text(encoding="utf-8")


def test_qc_manifest_and_performance_snapshot_bind_outputs_to_inputs() -> None:
    design_entry = _design_entries()["S1"]
    run_report = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entry,
        protein_sequences=PROTEIN_SEQUENCES,
    )
    policy = default_qc_threshold_policy()
    run_assessment = build_run_qc_assessment(run_report, policy=policy)
    benchmark = build_performance_snapshot(
        run_report.run_id,
        operations={
            "parse_fasta": (0.01, 2),
            "parse_psms": (0.02, 5),
            "parse_spectra": (0.03, 6),
            "build_run_qc": (0.01, 6),
        },
    )
    manifest = build_qc_evidence_manifest(
        run_report=run_report,
        run_assessment=run_assessment,
        policy=policy,
        input_files=(
            QcEvidenceInputFile(path="spectra.mgf", sha256="a" * 64, role="spectra"),
            QcEvidenceInputFile(
                path="results.tsv", sha256="b" * 64, role="identifications"
            ),
        ),
        benchmark=benchmark,
    )

    assert benchmark.total_elapsed_seconds == 0.07
    assert manifest.policy_name == "default-lcms-qc"
    assert manifest.run_report_sha256
    assert manifest.run_assessment_sha256
    assert manifest.benchmark_sha256


def test_qc_run_bundle_summary_joins_reports_and_evidence_metadata() -> None:
    design_entry = _design_entries()["S1"]
    run_report = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entry,
        protein_sequences=PROTEIN_SEQUENCES,
    )
    policy = default_qc_threshold_policy()
    run_assessment = build_run_qc_assessment(run_report, policy=policy)
    manifest = build_qc_evidence_manifest(
        run_report=run_report,
        run_assessment=run_assessment,
        policy=policy,
        input_files=(
            QcEvidenceInputFile(path="spectra.mgf", sha256="a" * 64, role="spectra"),
            QcEvidenceInputFile(
                path="results.tsv", sha256="b" * 64, role="identifications"
            ),
        ),
    )

    summary = build_qc_run_bundle_summary(
        run_report=run_report,
        run_assessment=run_assessment,
        evidence_manifest=manifest,
    )

    assert summary.run_id == "run-a"
    assert summary.policy_name == "default-lcms-qc"
    assert summary.qc_status is run_assessment.qc_status
    assert summary.evidence_file_roles == ("identifications", "spectra")
    assert summary.status_reason_codes
    assert "run_report" in summary.manifest_sha256s


def test_qc_publication_decision_refuses_failed_mandatory_gates() -> None:
    design_entries = _design_entries()
    run_a = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entries["S1"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_c = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entries["S3"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    policy = _strict_qc_policy()
    run_assessment = build_run_qc_assessment(run_c, policy=policy)
    batch_assessment = build_batch_qc_assessment(
        build_instrument_batch_qc_report((run_a, run_c)),
        policy=policy,
    )

    refused = build_qc_publication_decision(
        run_assessment=run_assessment,
        batch_assessment=batch_assessment,
    )
    allowed = build_qc_publication_decision(
        run_assessment=build_run_qc_assessment(
            run_a, policy=default_qc_threshold_policy()
        )
    )

    assert refused.publish_allowed is False
    assert refused.promote_allowed is False
    assert "identification_rate" in refused.blocking_metric_keys
    assert allowed.publish_allowed is True
