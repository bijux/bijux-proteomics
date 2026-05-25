# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.lab as lab
from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
)


def test_lab_package_exports_run_diagnosis_surface() -> None:
    rows = lab.classify_run_failure(
        (
            lab.RunDiagnosisQcEntry(
                run_id="run_reference",
                tic=1_000_000.0,
                bpc=150_000.0,
                ms1_count=1200,
                ms2_count=9000,
                id_count=1800,
                median_rt=1800.0,
                median_peak_width=12.0,
                missingness=0.08,
            ),
            lab.RunDiagnosisQcEntry(
                run_id="run_identification",
                tic=980_000.0,
                bpc=148_000.0,
                ms1_count=1190,
                ms2_count=9100,
                id_count=420,
                median_rt=1810.0,
                median_peak_width=12.5,
                missingness=0.10,
            ),
            lab.RunDiagnosisQcEntry(
                run_id="run_signal",
                tic=320_000.0,
                bpc=41_000.0,
                ms1_count=520,
                ms2_count=6700,
                id_count=980,
                median_rt=1790.0,
                median_peak_width=12.3,
                missingness=0.31,
            ),
        )
    )
    rendered = lab.render_run_diagnosis_tsv(rows)

    assert hasattr(lab, "classify_run_failure")
    assert hasattr(lab, "render_run_diagnosis_tsv")
    assert any(
        row.failure_class is lab.RunFailureClass.IDENTIFICATION_FAILURE for row in rows
    )
    assert "secondary_reasons" in rendered


def test_lab_package_exports_digestion_diagnosis_surface() -> None:
    rows = lab.classify_digestion(
        (
            lab.DigestionPeptideObservation(
                sample_id="sample_tryptic",
                peptide_sequence="PEPTIDER",
                left_flank=None,
                right_flank="A",
            ),
            lab.DigestionPeptideObservation(
                sample_id="sample_tryptic",
                peptide_sequence="AAAQK",
                left_flank=None,
                right_flank="L",
            ),
            lab.DigestionPeptideObservation(
                sample_id="sample_mismatch",
                peptide_sequence="ARAAK",
                left_flank=None,
                right_flank="L",
            ),
            lab.DigestionPeptideObservation(
                sample_id="sample_mismatch",
                peptide_sequence="QQRAK",
                left_flank=None,
                right_flank="A",
            ),
            lab.DigestionPeptideObservation(
                sample_id="sample_mismatch",
                peptide_sequence="LMRAK",
                left_flank=None,
                right_flank="Q",
            ),
        ),
        declared_enzyme="trypsin",
    )
    rendered = lab.render_digestion_diagnosis_tsv(rows)

    assert hasattr(lab, "classify_digestion")
    assert hasattr(lab, "render_digestion_diagnosis_tsv")
    assert any(
        row.digestion_status is lab.DigestionStatus.ENZYME_MISMATCH for row in rows
    )
    assert "digestion_status" in rendered


def test_lab_package_exports_contamination_classification_surface() -> None:
    rows = lab.classify_contamination(
        (
            lab.ContaminantEvidenceEntry(
                sample_id="sample_standard",
                protein_ref="CON__ALBU_BOVIN",
                intensity=1600.0,
                sample_total_intensity=10_000.0,
            ),
            lab.ContaminantEvidenceEntry(
                sample_id="sample_unknown",
                protein_ref="CON__Q9UNKNOWN",
                intensity=800.0,
                sample_total_intensity=10_000.0,
            ),
        ),
        (
            lab.ContaminantAnnotationEntry(
                protein_ref="CON__ALBU_BOVIN",
                contaminant_class=lab.ContaminantClass.STANDARD,
            ),
        ),
    )
    rendered = lab.render_contamination_classification_tsv(rows)

    assert hasattr(lab, "classify_contamination")
    assert hasattr(lab, "render_contamination_classification_tsv")
    assert any(row.contaminant_class is lab.ContaminantClass.STANDARD for row in rows)
    assert any(row.contaminant_class is lab.ContaminantClass.UNKNOWN for row in rows)
    assert "action_hint" in rendered


def test_lab_package_exports_background_comparison_surface() -> None:
    matrix = QuantMatrix(
        matrix_id="background_surface_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("P_blank_heavy", "P_biological"),
        sample_ids=("blank_a", "sample_1"),
        values=((1200.0, 1500.0), (20.0, 2200.0)),
        missing_value_states=(
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
        ),
        support_counts=((1, 1), (1, 1)),
    )

    rows = lab.compare_samples_to_blanks(matrix, blank_runs=("blank_a",))
    rendered = lab.render_background_comparison_tsv(rows)

    assert hasattr(lab, "compare_samples_to_blanks")
    assert hasattr(lab, "render_background_comparison_tsv")
    assert any(row.background_flag is True for row in rows)
    assert "background_flag" in rendered


def test_lab_package_exports_internal_standard_tracking_surface() -> None:
    matrix = QuantMatrix(
        matrix_id="internal_standard_surface_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("STD_A", "STD_B"),
        sample_ids=("sample_a", "sample_b", "sample_c"),
        values=((1000.0, 980.0, 620.0), (500.0, 510.0, 505.0)),
        missing_value_states=(
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
        ),
        support_counts=((1, 1, 1), (1, 1, 1)),
    )

    rows = lab.track_internal_standards(matrix, ("STD_A", "STD_B"))
    qc_rows = lab.build_internal_standard_sample_qc(rows)
    rendered = lab.render_internal_standard_tracking_tsv(rows)

    assert hasattr(lab, "track_internal_standards")
    assert hasattr(lab, "build_internal_standard_sample_qc")
    assert hasattr(lab, "render_internal_standard_tracking_tsv")
    assert any(row.drift_flag is True for row in rows)
    assert any(row.qc_status.value == "caution" for row in qc_rows)
    assert "drift_flag" in rendered
