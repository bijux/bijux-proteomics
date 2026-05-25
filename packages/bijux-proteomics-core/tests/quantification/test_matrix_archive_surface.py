# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMeasureKind,
    QuantMatrix,
    SampleMetadata,
)
from bijux_proteomics.quantification.matrix_archive import (
    QuantMatrixArchive,
    load_matrix_archive,
    render_quant_matrix_archive_tsv,
    save_matrix_archive,
)


def test_matrix_archive_preserves_masks_metadata_and_transformation_history(
    tmp_path: Path,
) -> None:
    matrix = QuantMatrix(
        matrix_id="protein_archive",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.LOG2_ABUNDANCE,
        entity_ids=("P001", "P002"),
        sample_ids=("sample-a", "sample-b"),
        values=((10.5, None), (9.1, 7.4)),
        missing_value_states=(
            (MissingValueState.OBSERVED, MissingValueState.NOT_OBSERVED),
            (MissingValueState.ZERO, MissingValueState.FILTERED),
        ),
        support_counts=((3, 0), (2, 1)),
        row_metadata=(
            {"protein_refs": "P001", "gene": "GENE1"},
            {"protein_refs": "P002", "gene": "GENE2"},
        ),
        sample_metadata=(
            SampleMetadata(
                sample_id="sample-a",
                run_id="run-a",
                condition="control",
                replicate=1,
                batch="batch-a",
            ),
            SampleMetadata(
                sample_id="sample-b",
                run_id="run-b",
                condition="case",
                replicate=1,
                instrument="orbitrap",
            ),
        ),
        transformation_history=("normalization:median", "imputation:low_intensity"),
        metadata={"scale": "log2"},
    )
    archive_path = tmp_path / "matrix_archive.json"

    archive = save_matrix_archive(matrix, archive_path)
    loaded = load_matrix_archive(archive_path)

    assert archive_path.exists()
    assert archive.missing_mask == ((False, True), (False, True))
    assert archive.imputation_mask == ((False, False), (False, True))
    assert loaded == archive
    assert loaded.to_quant_matrix() == matrix
    assert loaded.sample_metadata[1].instrument == "orbitrap"
    assert loaded.transformation_history[-1] == "imputation:low_intensity"


def test_matrix_archive_round_trip_stays_byte_stable_for_tsv_and_json_exports(
    tmp_path: Path,
) -> None:
    matrix = QuantMatrix(
        matrix_id="peptide_archive",
        entity_kind=QuantEntityKind.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("PEP_A",),
        sample_ids=("sample-a", "sample-b"),
        values=((1250.0, 980.0),),
        missing_value_states=(
            (MissingValueState.OBSERVED, MissingValueState.FILTERED),
        ),
        support_counts=((2, 1),),
        row_metadata=({"protein_refs": "P11111", "member_peptides": "PEP_A"},),
        sample_metadata=(
            SampleMetadata(
                sample_id="sample-a",
                run_id="run-a",
                condition="control",
                replicate=1,
            ),
            SampleMetadata(
                sample_id="sample-b",
                run_id="run-b",
                condition="case",
                replicate=1,
            ),
        ),
        transformation_history=("aggregation:sum", "imputation:reference_group"),
    )
    first_path = tmp_path / "matrix_archive_first.json"
    second_path = tmp_path / "matrix_archive_second.json"

    save_matrix_archive(matrix, first_path)
    reloaded = load_matrix_archive(first_path)
    save_matrix_archive(reloaded, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert (
        matrix.to_stable_json() + "\n"
        == reloaded.to_quant_matrix().to_stable_json() + "\n"
    )
    assert render_quant_matrix_archive_tsv(matrix) == render_quant_matrix_archive_tsv(
        reloaded
    )

    archive = QuantMatrixArchive.model_validate_json(
        first_path.read_text(encoding="utf-8")
    )
    assert archive.document_schema.document_kind == "quant_matrix_archive"
