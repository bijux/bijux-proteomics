# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.workflow.cohort_stratification import (
    CohortInteractionCandidateKind,
    CohortStratificationField,
    CohortStratumStatus,
    build_cohort_stratification_report,
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="MC1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="mc1.mzml",
            batch="batch-a",
            metadata={"sex": "male"},
        ),
        ExperimentalDesignEntry(
            sample_id="MC2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="mc2.mzml",
            batch="batch-b",
            metadata={"sex": "male"},
        ),
        ExperimentalDesignEntry(
            sample_id="MT1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="mt1.mzml",
            batch="batch-a",
            metadata={"sex": "male"},
        ),
        ExperimentalDesignEntry(
            sample_id="MT2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="mt2.mzml",
            batch="batch-b",
            metadata={"sex": "male"},
        ),
        ExperimentalDesignEntry(
            sample_id="FC1",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="fc1.mzml",
            batch="batch-c",
            metadata={"sex": "female"},
        ),
        ExperimentalDesignEntry(
            sample_id="FC2",
            condition="control",
            replicate=4,
            fraction=1,
            spectra_file="fc2.mzml",
            batch="batch-d",
            metadata={"sex": "female"},
        ),
        ExperimentalDesignEntry(
            sample_id="FT1",
            condition="treatment",
            replicate=3,
            fraction=1,
            spectra_file="ft1.mzml",
            batch="batch-c",
            metadata={"sex": "female"},
        ),
        ExperimentalDesignEntry(
            sample_id="FT2",
            condition="treatment",
            replicate=4,
            fraction=1,
            spectra_file="ft2.mzml",
            batch="batch-d",
            metadata={"sex": "female"},
        ),
    )


def _table() -> LabelFreeQuantTable:
    intensity_by_protein = {
        "P04637": {
            "MC1": 100.0,
            "MC2": 110.0,
            "MT1": 1000.0,
            "MT2": 1100.0,
            "FC1": 200.0,
            "FC2": 210.0,
            "FT1": 205.0,
            "FT2": 215.0,
        },
        "O14920": {
            "MC1": 300.0,
            "MC2": 310.0,
            "MT1": 320.0,
            "MT2": 315.0,
            "FC1": 120.0,
            "FC2": 130.0,
            "FT1": 1000.0,
            "FT2": 1050.0,
        },
        "Q9Y243": {
            "MC1": 400.0,
            "MC2": 420.0,
            "MT1": 900.0,
            "MT2": 920.0,
            "FC1": 380.0,
            "FC2": 390.0,
            "FT1": 840.0,
            "FT2": 860.0,
        },
        "P62993": {
            "MC1": 500.0,
            "MC2": 520.0,
            "MT1": 1100.0,
            "MT2": 1120.0,
            "FC1": 600.0,
            "FC2": 620.0,
            "FT1": 180.0,
            "FT2": 190.0,
        },
        "Q8N158": {
            "MC1": 700.0,
            "MC2": 710.0,
            "MT1": 720.0,
            "MT2": 730.0,
            "FC1": 705.0,
            "FC2": 715.0,
            "FT1": 710.0,
            "FT2": 720.0,
        },
    }
    records: list[Ms1FeatureRecord] = []
    for index, (protein_ref, values_by_sample) in enumerate(
        intensity_by_protein.items(),
        start=1,
    ):
        peptide = f"PEP{index:02d}"
        for sample_id, intensity in values_by_sample.items():
            records.append(
                Ms1FeatureRecord(
                    feature_id=f"cohort-{index:03d}-{sample_id.lower()}",
                    sample_id=sample_id,
                    peptide=peptide,
                    canonical_peptide=peptide,
                    intensity=intensity,
                    protein_refs=(protein_ref,),
                    missing_value_kind=MissingValueKind.OBSERVED,
                )
            )
    return build_label_free_intensity_table(
        tuple(records),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_cohort_stratification_blocks_sparse_batch_strata_and_preserves_supported_sex_effects() -> (
    None
):
    report = build_cohort_stratification_report(
        _table(),
        _design(),
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.field_count == 2
    assert report.summary.supported_stratum_count == 2
    assert report.summary.blocked_stratum_count == 4
    sex_entries = {
        entry.subgroup_value: entry
        for entry in report.stratum_entries
        if entry.field_name is CohortStratificationField.SEX
    }
    assert set(sex_entries) == {"female", "male"}
    assert all(
        entry.status is CohortStratumStatus.SUPPORTED for entry in sex_entries.values()
    )
    assert sex_entries["male"].sample_count_a == 2
    assert sex_entries["male"].sample_count_b == 2
    batch_entries = tuple(
        entry
        for entry in report.stratum_entries
        if entry.field_name is CohortStratificationField.BATCH
    )
    assert len(batch_entries) == 4
    assert all(
        entry.status is CohortStratumStatus.BLOCKED_LOW_SUBGROUP_SAMPLE_COUNT
        for entry in batch_entries
    )
    assert all(
        entry.field_name is CohortStratificationField.SEX
        for entry in report.subgroup_effect_entries
    )
    assert any(
        entry.subgroup_value == "male" and entry.entity_id == "P04637"
        for entry in report.subgroup_effect_entries
    )
    assert any(
        entry.subgroup_value == "female" and entry.entity_id == "O14920"
        for entry in report.subgroup_effect_entries
    )


def test_cohort_stratification_reports_interaction_candidates_and_deterministic_tsvs() -> (
    None
):
    report = build_cohort_stratification_report(
        _table(),
        _design(),
        condition_a="control",
        condition_b="treatment",
    )

    by_entity = {entry.entity_id: entry for entry in report.interaction_candidates}
    assert by_entity["P04637"].candidate_kind is (
        CohortInteractionCandidateKind.MAGNITUDE_DIFFERENCE
    )
    assert by_entity["P62993"].candidate_kind is (
        CohortInteractionCandidateKind.DIRECTION_CONFLICT
    )
    assert (
        by_entity["P62993"].left_log2_fold_change
        * by_entity["P62993"].right_log2_fold_change
        < 0
    )
    assert "blocked_stratum_count" in render_cohort_stratification_summary_tsv(report)
    assert "blocked_low_subgroup_sample_count" in render_cohort_stratum_tsv(report)
    assert "robustness_score" in render_cohort_subgroup_effect_tsv(report)
    interaction_tsv = render_cohort_interaction_candidate_tsv(report)
    assert "candidate_kind" in interaction_tsv
    assert "direction_conflict" in interaction_tsv
