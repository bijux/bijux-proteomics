# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectDirection,
    CrossStudyProteinEffectObservation,
)
from bijux_proteomics.workflow.cross_study_meta_analysis import (
    CrossStudyMetaAnalysisEffectModel,
    CrossStudyMetaAnalysisHeterogeneityTier,
    CrossStudyMetaAnalysisPolicy,
    CrossStudyMetaAnalysisRejectionReason,
    build_cross_study_meta_analysis_report_from_observations,
    render_cross_study_meta_analysis_rejected_tsv,
    render_cross_study_meta_analysis_study_weight_tsv,
    render_cross_study_meta_analysis_tsv,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinObservationSourceKind,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind


def _observation(
    *,
    observation_id: str,
    study_id: str,
    representative_protein_ref: str,
    accession_aliases: tuple[str, ...] = (),
    species: str = "Homo sapiens",
    condition_a: str = "treated",
    condition_b: str = "control",
    log2_fold_change: float,
    direction: CrossStudyEffectDirection,
    p_value: float,
    adjusted_p_value: float,
    standard_error: float | None,
) -> CrossStudyProteinEffectObservation:
    return CrossStudyProteinEffectObservation(
        observation_id=observation_id,
        study_id=study_id,
        study_label=study_id,
        study_kind=ProteomicsStudyKind.LABEL_FREE,
        species=species,
        source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
        source_surface="protein_cards",
        source_entity_id=observation_id,
        representative_protein_ref=representative_protein_ref,
        protein_refs=(representative_protein_ref,),
        accession_aliases=accession_aliases,
        gene_symbol="STAT1",
        condition_a=condition_a,
        condition_b=condition_b,
        log2_fold_change=log2_fold_change,
        direction=direction,
        p_value=p_value,
        adjusted_p_value=adjusted_p_value,
        standard_error=standard_error,
        confidence_interval_low=(
            None if standard_error is None else log2_fold_change - 1.96 * standard_error
        ),
        confidence_interval_high=(
            None if standard_error is None else log2_fold_change + 1.96 * standard_error
        ),
        robustness_score=0.8,
        significant=True,
        note=f"{study_id} effect",
    )


def test_cross_study_meta_analysis_combines_effects_with_inverse_variance_weights() -> (
    None
):
    report = build_cross_study_meta_analysis_report_from_observations(
        (
            _observation(
                observation_id="study_a:protein_1",
                study_id="study_a",
                representative_protein_ref="P11111",
                log2_fold_change=1.2,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
            ),
            _observation(
                observation_id="study_b:protein_1",
                study_id="study_b",
                representative_protein_ref="A0A0HUMAN1",
                accession_aliases=("P11111",),
                log2_fold_change=0.8,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.004,
                adjusted_p_value=0.02,
                standard_error=0.4,
            ),
        )
    )

    assert report.summary.combined_entry_count == 1
    assert report.summary.rejected_group_count == 0
    entry = report.combined_entries[0]
    assert (
        entry.effect_model is CrossStudyMetaAnalysisEffectModel.FIXED_INVERSE_VARIANCE
    )
    assert entry.combined_log2_fold_change == pytest.approx(1.12)
    assert entry.combined_standard_error == pytest.approx((1.0 / 31.25) ** 0.5)
    assert entry.heterogeneity_i_squared == pytest.approx(0.0)
    assert entry.combined_p_value < 1e-6
    assert entry.combined_p_value != pytest.approx((0.001 + 0.004) / 2.0)

    weight_by_study = {
        weight_entry.study_id: weight_entry
        for weight_entry in report.study_weight_entries
    }
    assert weight_by_study["study_a"].fixed_weight_fraction == pytest.approx(0.8)
    assert weight_by_study["study_b"].fixed_weight_fraction == pytest.approx(0.2)

    rendered = render_cross_study_meta_analysis_tsv(report)
    assert "combined_log2_fold_change" in rendered
    assert "between_study_variance_tau_squared" in rendered
    assert "fixed_weight_fraction" in render_cross_study_meta_analysis_study_weight_tsv(
        report
    )


def test_cross_study_meta_analysis_marks_direction_conflicts_and_high_heterogeneity() -> (
    None
):
    report = build_cross_study_meta_analysis_report_from_observations(
        (
            _observation(
                observation_id="study_a:protein_2",
                study_id="study_a",
                representative_protein_ref="P22222",
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
            ),
            _observation(
                observation_id="study_b:protein_2",
                study_id="study_b",
                representative_protein_ref="A0A0HUMAN2",
                accession_aliases=("P22222",),
                log2_fold_change=-0.9,
                direction=CrossStudyEffectDirection.DOWN,
                p_value=0.002,
                adjusted_p_value=0.02,
                standard_error=0.2,
            ),
        )
    )

    entry = report.combined_entries[0]
    assert entry.direction_conflict is True
    assert set(entry.conflicting_study_ids) == {"study_a", "study_b"}
    assert entry.effect_model is CrossStudyMetaAnalysisEffectModel.RANDOM_EFFECTS
    assert entry.heterogeneity_tier is CrossStudyMetaAnalysisHeterogeneityTier.HIGH


def test_cross_study_meta_analysis_rejects_heterogeneous_contrasts() -> None:
    report = build_cross_study_meta_analysis_report_from_observations(
        (
            _observation(
                observation_id="study_a:protein_3",
                study_id="study_a",
                representative_protein_ref="P33333",
                log2_fold_change=1.1,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
            ),
            _observation(
                observation_id="study_b:protein_3",
                study_id="study_b",
                representative_protein_ref="A0A0HUMAN3",
                accession_aliases=("P33333",),
                condition_a="resistant",
                condition_b="sensitive",
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                standard_error=0.3,
            ),
        )
    )

    assert report.combined_entries == ()
    assert report.summary.rejected_group_count == 1
    rejected = report.rejected_entries[0]
    assert (
        rejected.rejection_reason
        is CrossStudyMetaAnalysisRejectionReason.HETEROGENEOUS_CONTRASTS
    )
    assert "heterogeneous_contrasts" in render_cross_study_meta_analysis_rejected_tsv(
        report
    )


def test_cross_study_meta_analysis_rejects_missing_standard_error() -> None:
    report = build_cross_study_meta_analysis_report_from_observations(
        (
            _observation(
                observation_id="study_a:protein_4",
                study_id="study_a",
                representative_protein_ref="P44444",
                log2_fold_change=1.1,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
            ),
            _observation(
                observation_id="study_b:protein_4",
                study_id="study_b",
                representative_protein_ref="A0A0HUMAN4",
                accession_aliases=("P44444",),
                log2_fold_change=0.9,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                standard_error=None,
            ),
        )
    )

    assert report.combined_entries == ()
    assert report.rejected_entries[0].rejection_reason is (
        CrossStudyMetaAnalysisRejectionReason.MISSING_STANDARD_ERROR
    )


def test_cross_study_meta_analysis_rejects_mixed_species_without_policy() -> None:
    report = build_cross_study_meta_analysis_report_from_observations(
        (
            _observation(
                observation_id="human:protein_5",
                study_id="human",
                representative_protein_ref="P55555",
                species="Homo sapiens",
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
            ),
            _observation(
                observation_id="mouse:protein_5",
                study_id="mouse",
                representative_protein_ref="P55555",
                species="Mus musculus",
                log2_fold_change=0.8,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                standard_error=0.3,
            ),
        ),
        policy=CrossStudyMetaAnalysisPolicy(allow_cross_species=False),
    )

    assert report.combined_entries == ()
    assert report.rejected_entries[0].rejection_reason is (
        CrossStudyMetaAnalysisRejectionReason.MIXED_SPECIES_GROUP
    )
