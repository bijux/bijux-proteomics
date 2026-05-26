# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_quant_design_matrix_report,
    export_quant_design_contrast_estimates_tsv,
    export_quant_design_matrix_tsv,
    export_quant_design_model_coefficients_tsv,
    fit_quant_design_matrix_model,
    render_quant_design_contrast_estimates_tsv,
    render_quant_design_matrix_tsv,
    render_quant_design_model_coefficients_tsv,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
            batch="batch-a",
            pair_id="pair-a",
            metadata={"sex": "female"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-a",
            pair_id="pair-a",
            metadata={"sex": "female"},
        ),
    )


def _table():
    records = (
        Ms1FeatureRecord(
            feature_id="f1",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f2",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=200.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_design_matrix_and_model_exports_render_stable_tsvs(tmp_path: Path) -> None:
    design_matrix = build_quant_design_matrix_report(
        _design(),
        batch_field="batch",
        pairing_field="pair_id",
    )
    fit_report = fit_quant_design_matrix_model(_table(), design_matrix)

    matrix_tsv = render_quant_design_matrix_tsv(design_matrix)
    coefficient_tsv = render_quant_design_model_coefficients_tsv(fit_report)
    contrast_tsv = render_quant_design_contrast_estimates_tsv(fit_report)

    assert matrix_tsv.startswith(
        "sample_id\tcondition\tbatch\tpair_id\tanalysis_sample_id\tbiological_sample_id\t"
        "run_ids\tsample_run_policy\tsex\ttechnical_replicate_ids\tintercept"
    )
    assert "condition[treatment]" in matrix_tsv
    assert coefficient_tsv.startswith("entity_id\tcoefficient_name\testimate")
    assert "P001\tcondition[treatment]" in coefficient_tsv
    assert contrast_tsv.startswith(
        "entity_id\tcontrast_name\tcondition_a\tcondition_b\testimate"
    )
    assert "P001\tcontrol_vs_treatment" in contrast_tsv

    matrix_path = tmp_path / "design_matrix.tsv"
    coefficient_path = tmp_path / "design_coefficients.tsv"
    contrast_path = tmp_path / "design_contrasts.tsv"
    export_quant_design_matrix_tsv(design_matrix, matrix_path)
    export_quant_design_model_coefficients_tsv(fit_report, coefficient_path)
    export_quant_design_contrast_estimates_tsv(fit_report, contrast_path)

    assert matrix_path.read_text(encoding="utf-8") == matrix_tsv
    assert coefficient_path.read_text(encoding="utf-8") == coefficient_tsv
    assert contrast_path.read_text(encoding="utf-8") == contrast_tsv
