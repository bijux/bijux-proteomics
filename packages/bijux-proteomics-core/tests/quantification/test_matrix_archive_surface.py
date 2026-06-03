# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import string
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
    SampleMetadata,
)
from bijux_proteomics.quantification.matrix_archive import (
    QuantMatrixArchive,
    load_matrix_archive,
    render_quant_matrix_archive_tsv,
    save_matrix_archive,
)
from bijux_proteomics_foundation.testing.skip_policy import (
    import_hypothesis_or_skip,
)

if TYPE_CHECKING:
    from hypothesis import given, settings
    from hypothesis import strategies as st
else:
    hypothesis = import_hypothesis_or_skip(
        reason="hypothesis is required for the matrix archive property-based surface",
    )
    given = hypothesis.given
    settings = hypothesis.settings
    st = hypothesis.strategies

_SAFE_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "-_./",
    min_size=1,
    max_size=12,
).filter(
    lambda value: value.strip().lower() not in {"", "na", "n/a", "null", "none", "nan"}
)
_OPTIONAL_TEXT = st.one_of(st.none(), _SAFE_TEXT)
_SMALL_FLOAT = st.integers(min_value=-10_000, max_value=10_000).map(
    lambda value: value / 10.0
)
_MATRIX_VALUE = st.one_of(st.none(), _SMALL_FLOAT)
_METADATA_MAP = st.dictionaries(_SAFE_TEXT, _SAFE_TEXT, max_size=3)


@st.composite
def _quant_matrix_strategy(draw: st.DrawFn) -> QuantMatrix:
    entity_ids = tuple(draw(st.lists(_SAFE_TEXT, min_size=1, max_size=4, unique=True)))
    sample_ids = tuple(draw(st.lists(_SAFE_TEXT, min_size=1, max_size=4, unique=True)))
    values = tuple(tuple(draw(_MATRIX_VALUE) for _ in sample_ids) for _ in entity_ids)
    missing_value_states = tuple(
        tuple(draw(st.sampled_from(tuple(MissingValueState))) for _ in sample_ids)
        for _ in entity_ids
    )
    support_counts = tuple(
        tuple(draw(st.integers(min_value=0, max_value=5)) for _ in sample_ids)
        for _ in entity_ids
    )
    row_metadata = tuple(draw(_METADATA_MAP) for _ in entity_ids)
    sample_metadata = tuple(
        SampleMetadata(
            sample_id=sample_id,
            run_id=f"{sample_id}.mzML",
            condition=draw(_SAFE_TEXT),
            replicate=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=3))),
            fraction=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=2))),
            batch=draw(_OPTIONAL_TEXT),
            instrument=draw(_OPTIONAL_TEXT),
            search_engine=draw(_OPTIONAL_TEXT),
            metadata=draw(st.dictionaries(_SAFE_TEXT, _SAFE_TEXT, max_size=2)),
        )
        for sample_id in sample_ids
    )
    return QuantMatrix(
        matrix_id=draw(_SAFE_TEXT),
        entity_kind=draw(st.sampled_from(tuple(QuantEntityKind))),
        measure_kind=draw(st.sampled_from(tuple(QuantMeasureKind))),
        entity_ids=entity_ids,
        sample_ids=sample_ids,
        values=values,
        missing_value_states=missing_value_states,
        support_counts=support_counts,
        row_metadata=row_metadata,
        sample_metadata=sample_metadata,
        transformation_history=tuple(
            draw(st.lists(_SAFE_TEXT, max_size=3, unique=True))
        ),
        metadata=draw(st.dictionaries(_SAFE_TEXT, _SAFE_TEXT, max_size=3)),
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
            (MissingValueState.OBSERVED, MissingValueState.CENSORED),
            (MissingValueState.ZERO, MissingValueState.IMPUTED),
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
    assert archive.missing_mask == ((False, True), (False, False))
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


@given(matrix=_quant_matrix_strategy())
@settings(deadline=None, max_examples=25)
def test_matrix_archive_round_trips_generated_quant_matrices(
    matrix: QuantMatrix,
) -> None:
    with TemporaryDirectory() as temp_dir:
        first_path = Path(temp_dir) / "matrix_archive_first.json"
        second_path = Path(temp_dir) / "matrix_archive_second.json"

        archive = save_matrix_archive(matrix, first_path)
        reloaded = load_matrix_archive(first_path)
        save_matrix_archive(reloaded, second_path)

        assert first_path.read_bytes() == second_path.read_bytes()
        assert reloaded == archive
        assert reloaded.to_quant_matrix() == matrix
        assert render_quant_matrix_archive_tsv(
            matrix
        ) == render_quant_matrix_archive_tsv(reloaded)


@given(matrix=_quant_matrix_strategy())
@settings(deadline=None, max_examples=25)
def test_matrix_archive_generated_masks_and_cell_ledger_match_matrix_semantics(
    matrix: QuantMatrix,
) -> None:
    with TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "matrix_archive.json"
        archive = save_matrix_archive(matrix, archive_path)

        expected_missing_mask = tuple(
            tuple(
                state
                in {
                    MissingValueState.NOT_OBSERVED,
                    MissingValueState.FILTERED,
                    MissingValueState.CENSORED,
                    MissingValueState.EXCLUDED,
                }
                for state in row
            )
            for row in matrix.missing_value_states
        )
        expected_imputation_mask = tuple(
            tuple(
                value is not None and state is MissingValueState.IMPUTED
                for value, state in zip(value_row, state_row, strict=False)
            )
            for value_row, state_row in zip(
                matrix.values,
                matrix.missing_value_states,
                strict=False,
            )
        )
        ledger_lines = render_quant_matrix_archive_tsv(archive).splitlines()

        assert archive.missing_mask == expected_missing_mask
        assert archive.imputation_mask == expected_imputation_mask
        assert ledger_lines[0].startswith("entity_id\tsample_id\tabundance\t")
        assert len(ledger_lines) == 1 + len(matrix.entity_ids) * len(matrix.sample_ids)
