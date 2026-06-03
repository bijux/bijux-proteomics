# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    build_proteomics_study_result,
    build_tmt_experiment_workflow_bundle,
)
from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectComparisonStatus,
    CrossStudyEffectContrastAlignmentStatus,
    CrossStudyEffectDirection,
    CrossStudyProteinEffectObservation,
    CrossStudyProteinStudyInput,
    build_cross_study_effect_comparison_report_from_observations,
    extract_cross_study_protein_effect_observations,
    render_cross_study_conflicting_hit_tsv,
    render_cross_study_effect_comparison_tsv,
    render_cross_study_effect_detail_tsv,
    render_cross_study_replicated_hit_tsv,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinObservationSourceKind,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_extract_cross_study_protein_effect_observations_preserves_biological_and_tmt_surfaces() -> (
    None
):
    biological_design = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        build_experiment_design(biological_design),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    tmt_workflow = build_tmt_experiment_workflow_bundle(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        _multiplex_fixture("tmt.design.tsv"),
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
        condition_a="control",
        condition_b="treatment",
        batch_field="",
    )

    extraction = extract_cross_study_protein_effect_observations(
        (
            CrossStudyProteinStudyInput(
                study_id="label_free_study",
                study_result=build_proteomics_study_result(biological_report),
            ),
            CrossStudyProteinStudyInput(
                study_id="tmt_study",
                study_result=build_proteomics_study_result(tmt_workflow),
                species="Homo sapiens",
            ),
        )
    )

    assert extraction.summary.supported_study_count == 2
    assert extraction.summary.observation_count >= 2
    assert extraction.unsupported_studies == ()
    protein_card_entry = next(
        entry
        for entry in extraction.observations
        if entry.source_surface == "protein_cards"
    )
    label_based_entry = next(
        entry
        for entry in extraction.observations
        if entry.source_surface == "label_based_differential_report"
    )
    assert protein_card_entry.standard_error is not None
    assert protein_card_entry.confidence_interval_low is not None
    assert protein_card_entry.confidence_interval_high is not None
    assert label_based_entry.standard_error is not None
    assert label_based_entry.confidence_interval_low is not None
    assert label_based_entry.confidence_interval_high is not None

    comparison_report = build_cross_study_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_detail",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_detail",
                representative_protein_ref="P99991",
                protein_refs=("P99991",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.1,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
                confidence_interval_low=0.708,
                confidence_interval_high=1.492,
                robustness_score=0.82,
                significant=True,
                note="study a effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_detail",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_detail",
                representative_protein_ref="A0A0HUMAN9",
                protein_refs=("A0A0HUMAN9",),
                accession_aliases=("P99991",),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.9,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                standard_error=0.3,
                confidence_interval_low=0.312,
                confidence_interval_high=1.488,
                robustness_score=0.76,
                significant=True,
                note="study b effect",
            ),
        )
    )
    detail_entry = next(
        entry
        for entry in comparison_report.study_entries
        if entry.standard_error is not None
    )
    assert detail_entry.standard_error is not None
    assert detail_entry.confidence_interval_low is not None
    assert detail_entry.confidence_interval_high is not None
    detail_tsv = render_cross_study_effect_detail_tsv(comparison_report)
    assert "standard_error" in detail_tsv
    assert "confidence_interval_low" in detail_tsv
    assert "confidence_interval_high" in detail_tsv


def test_cross_study_effect_comparison_marks_replicated_hits_after_reversed_contrast_normalization() -> (
    None
):
    report = build_cross_study_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_1",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.3,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.82,
                significant=True,
                note="study a effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_1",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="STAT1",
                condition_a="control",
                condition_b="treated",
                log2_fold_change=-1.1,
                direction=CrossStudyEffectDirection.DOWN,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.76,
                significant=True,
                note="study b reversed-order effect",
            ),
        )
    )

    assert len(report.comparisons) == 1
    comparison = report.comparisons[0]
    assert (
        comparison.contrast_alignment_status
        is CrossStudyEffectContrastAlignmentStatus.REVERSED_ORDER_NORMALIZED
    )
    assert (
        comparison.comparison_status is CrossStudyEffectComparisonStatus.REPLICATED_HIT
    )
    assert comparison.replicated_hit is True
    assert comparison.conflicting_hit is False
    assert set(comparison.normalized_significant_directions) == {
        CrossStudyEffectDirection.UP
    }
    assert "replicated_hit" in render_cross_study_replicated_hit_tsv(report)


def test_cross_study_effect_comparison_marks_conflicting_hits_explicitly() -> None:
    report = build_cross_study_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_2",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_2",
                representative_protein_ref="P22222",
                protein_refs=("P22222",),
                accession_aliases=(),
                gene_symbol="FOXO1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.1,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.90,
                significant=True,
                note="study a effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_2",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.MAXQUANT,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_2",
                representative_protein_ref="B0B0HUMAN2",
                protein_refs=("B0B0HUMAN2",),
                accession_aliases=("P22222",),
                gene_symbol="FOXO1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=-1.0,
                direction=CrossStudyEffectDirection.DOWN,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.88,
                significant=True,
                note="study b opposite effect",
            ),
        )
    )

    comparison = report.comparisons[0]
    assert (
        comparison.comparison_status is CrossStudyEffectComparisonStatus.CONFLICTING_HIT
    )
    assert comparison.conflicting_hit is True
    assert set(comparison.conflicting_study_ids) == {"study_a", "study_b"}
    assert "conflicting_hit" in render_cross_study_conflicting_hit_tsv(report)


def test_cross_study_effect_comparison_keeps_heterogeneous_contrasts_separate() -> None:
    report = build_cross_study_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_3",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_3",
                representative_protein_ref="P33333",
                protein_refs=("P33333",),
                accession_aliases=(),
                gene_symbol="JUN",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.75,
                significant=True,
                note="study a effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_3",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.TMT,
                species="Homo sapiens",
                source_kind=(
                    CrossStudyProteinObservationSourceKind.LABEL_BASED_DIFFERENTIAL_ROW
                ),
                source_surface="label_based_differential_report",
                source_entity_id="protein_3",
                representative_protein_ref="A0A0HUMAN3",
                protein_refs=("A0A0HUMAN3",),
                accession_aliases=("P33333",),
                gene_symbol="JUN",
                condition_a="resistant",
                condition_b="sensitive",
                log2_fold_change=1.1,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.003,
                adjusted_p_value=0.03,
                robustness_score=0.71,
                significant=True,
                note="study b different contrast",
            ),
        )
    )

    comparison = report.comparisons[0]
    assert (
        comparison.contrast_alignment_status
        is CrossStudyEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
    )
    assert (
        comparison.comparison_status
        is CrossStudyEffectComparisonStatus.HETEROGENEOUS_CONTRASTS
    )
    assert "heterogeneous_contrasts" in render_cross_study_effect_comparison_tsv(report)
