# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"

MISSINGNESS_COMPANION_OWNERS = {
    "dia/precursor_matrix.py": (
        "render_dia_precursor_quantity_matrix_tsv",
        "render_dia_precursor_missingness_tsv",
    ),
    "dia/protein_matrix.py": (
        "render_dia_peptide_quantity_matrix_tsv",
        "render_dia_peptide_missingness_tsv",
        "render_dia_protein_quantity_matrix_tsv",
        "render_dia_protein_missingness_tsv",
    ),
    "quantification/contracts/matrix_models.py": (
        "render_label_free_quant_missingness_matrix_tsv",
    ),
    "quantification/matrix/protein_intensity_matrix.py": (
        "render_protein_intensity_matrix_tsv",
        "render_protein_intensity_missingness_mask_tsv",
    ),
    "quantification/rollup/protein_lfq/rendering.py": (
        "render_protein_lfq_matrix_tsv",
        "render_protein_lfq_missingness_mask_tsv",
    ),
    "workflow/pipelines/dia_differential_analysis.py": (
        "render_dia_differential_matrix_tsv",
        "render_dia_differential_missingness_tsv",
    ),
    "workflow/pipelines/label_based_differential/rendering.py": (
        "render_label_based_differential_matrix_tsv",
        "render_label_based_differential_missingness_tsv",
    ),
}

MISSINGNESS_SIDE_CAR_EXPORT_OWNERS = {
    "workflow/pipelines/maxquant_biological_workflow.py": (
        "lfq_missingness_tsv",
        "render_label_free_quant_missingness_matrix_tsv",
    ),
    "workflow/pipelines/dda_biological_workflow.py": (
        "protein_lfq_missingness_tsv",
        "protein_lfq_missingness_mask_tsv",
    ),
    "workflow/pipelines/diann_biological_workflow.py": (
        "precursor_missingness_tsv",
        "peptide_missingness_tsv",
        "protein_missingness_tsv",
        "differential_raw_missingness_tsv",
        "differential_normalized_missingness_tsv",
    ),
}


def test_matrix_renderers_define_missingness_companion_surfaces() -> None:
    offenders: list[str] = []

    for relative_path, required_tokens in MISSINGNESS_COMPANION_OWNERS.items():
        source_text = (SOURCE_ROOT / relative_path).read_text(encoding="utf-8")
        missing = [token for token in required_tokens if token not in source_text]
        if missing:
            offenders.append(f"{relative_path}: missing {', '.join(missing)}")

    assert offenders == []


def test_workflow_matrix_export_owners_write_missingness_sidecars() -> None:
    offenders: list[str] = []

    for relative_path, required_tokens in MISSINGNESS_SIDE_CAR_EXPORT_OWNERS.items():
        source_text = (SOURCE_ROOT / relative_path).read_text(encoding="utf-8")
        missing = [token for token in required_tokens if token not in source_text]
        if missing:
            offenders.append(f"{relative_path}: missing {', '.join(missing)}")

    assert offenders == []
