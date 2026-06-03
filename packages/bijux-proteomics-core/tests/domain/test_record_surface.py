# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.domain import (
    Contrast,
    ContrastKind,
    MissingValueState,
    ProteinGroup,
    ProteinRecord,
    PSMRecord,
    PTMSite,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
    RejectedEvidence,
    SampleMetadata,
    SpectrumRecord,
    TargetDecoyState,
    TransitionRecord,
)


def test_domain_records_expose_fixed_required_field_contracts() -> None:
    assert ProteinRecord.documented_dict_required_fields() == (
        "record_id",
        "primary_protein_ref",
    )
    assert PSMRecord.documented_dict_required_fields() == (
        "spectrum_id",
        "peptide_sequence",
        "canonical_peptide",
        "charge_state",
        "score",
    )
    assert QuantMatrix.documented_dict_required_fields() == (
        "matrix_id",
        "entity_kind",
        "measure_kind",
    )


def test_quant_matrix_requires_aligned_sample_metadata_and_shapes() -> None:
    matrix = QuantMatrix(
        matrix_id="protein_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("P001",),
        sample_ids=("sample-a", "sample-b"),
        values=((10.0, None),),
        missing_value_states=(
            (MissingValueState.OBSERVED, MissingValueState.NOT_OBSERVED),
        ),
        support_counts=((2, 0),),
        row_metadata=({"protein_refs": "P001"},),
        sample_metadata=(
            SampleMetadata(
                sample_id="sample-a",
                run_id="run-a",
                condition="control",
            ),
            SampleMetadata(
                sample_id="sample-b",
                run_id="run-b",
                condition="treated",
            ),
        ),
    )

    assert matrix.sample_metadata[0].sample_id == "sample-a"
    assert matrix.values[0][1] is None
    assert matrix.support_counts == ((2, 0),)

    with pytest.raises(ValueError, match="sample_metadata sample_id order must match"):
        QuantMatrix(
            matrix_id="bad_matrix",
            entity_kind=QuantEntityKind.PROTEIN,
            measure_kind=QuantMeasureKind.INTENSITY,
            entity_ids=("P001",),
            sample_ids=("sample-a", "sample-b"),
            values=((10.0, None),),
            missing_value_states=(
                (MissingValueState.OBSERVED, MissingValueState.NOT_OBSERVED),
            ),
            sample_metadata=(
                SampleMetadata(
                    sample_id="sample-b",
                    run_id="run-b",
                    condition="treated",
                ),
                SampleMetadata(
                    sample_id="sample-a",
                    run_id="run-a",
                    condition="control",
                ),
            ),
        )

    with pytest.raises(ValueError, match="support_counts"):
        QuantMatrix(
            matrix_id="bad_support_counts",
            entity_kind=QuantEntityKind.PROTEIN,
            measure_kind=QuantMeasureKind.INTENSITY,
            entity_ids=("P001",),
            sample_ids=("sample-a", "sample-b"),
            values=((10.0, None),),
            missing_value_states=(
                (MissingValueState.OBSERVED, MissingValueState.NOT_OBSERVED),
            ),
            support_counts=((1,),),
        )


def test_domain_records_cover_shared_scientific_boundaries() -> None:
    assert (
        SpectrumRecord(
            spectrum_id="scan=1",
            precursor_mz=523.2,
            peak_count=24,
        ).spectrum_id
        == "scan=1"
    )
    assert (
        TransitionRecord(
            transition_id="y7",
            precursor_id="PEPTIDE/2",
            sample_id="sample-a",
            intensity=1250.0,
            peptide_sequence="PEPTIDE",
        ).intensity
        == 1250.0
    )
    assert (
        PTMSite(
            site_key="P001:S15:Phospho",
            protein_ref="P001",
            residue="S",
            position=15,
            modification_name="Phospho",
        ).position
        == 15
    )
    assert (
        ProteinGroup(
            group_id="group-1",
            representative_protein="P001",
            unique_peptide_count=1,
            shared_peptide_count=0,
        ).representative_protein
        == "P001"
    )
    assert (
        RejectedEvidence(
            record_kind="psm",
            rejection_reason="missing score",
        ).record_kind
        == "psm"
    )
    assert TargetDecoyState.TARGET.value == "target"


def test_contrast_records_require_kind_specific_semantic_fields() -> None:
    paired = Contrast(
        contrast_id="treated_vs_control_paired",
        left_condition="treated",
        right_condition="control",
        kind=ContrastKind.PAIRED,
        pair_id_field="pair_id",
    )
    time_course = Contrast(
        contrast_id="t1_vs_t0",
        left_condition="t1",
        right_condition="t0",
        kind=ContrastKind.TIME_COURSE,
        timepoint_field="timepoint",
    )
    multi_condition = Contrast(
        contrast_id="case_vs_control_multi",
        left_condition="case",
        right_condition="control",
        kind=ContrastKind.MULTI_CONDITION,
        condition_set=("case", "control", "rescue"),
    )

    assert paired.pair_id_field == "pair_id"
    assert time_course.timepoint_field == "timepoint"
    assert multi_condition.condition_set == ("case", "control", "rescue")

    with pytest.raises(ValueError, match="paired contrasts require pair_id_field"):
        Contrast(
            contrast_id="bad_paired",
            left_condition="treated",
            right_condition="control",
            kind=ContrastKind.PAIRED,
        )

    with pytest.raises(
        ValueError, match="time-course contrasts require timepoint_field"
    ):
        Contrast(
            contrast_id="bad_time_course",
            left_condition="t1",
            right_condition="t0",
            kind=ContrastKind.TIME_COURSE,
        )

    with pytest.raises(
        ValueError,
        match="multi-condition contrasts require at least three declared conditions",
    ):
        Contrast(
            contrast_id="bad_multi_condition",
            left_condition="case",
            right_condition="control",
            kind=ContrastKind.MULTI_CONDITION,
            condition_set=("case", "control"),
        )
