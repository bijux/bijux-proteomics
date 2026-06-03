# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.ortholog_mapping import (
    OrthologMappingCardinality,
    OrthologRecord,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    build_proteomics_study_result,
    build_tmt_experiment_workflow_bundle,
)
from bijux_proteomics.workflow.cross_species_effect_comparison import (
    CrossSpeciesEffectContrastAlignmentStatus,
    CrossSpeciesEffectEvidenceStatus,
    CrossSpeciesOrthologAmbiguityStatus,
    build_cross_species_effect_comparison_report,
    build_cross_species_effect_comparison_report_from_observations,
    render_cross_species_effect_comparison_tsv,
)
from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectDirection,
    CrossStudyProteinEffectObservation,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinObservationSourceKind,
    CrossStudyProteinStudyInput,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_cross_species_effect_comparison_preserves_one_to_many_ortholog_rows() -> None:
    report = build_cross_species_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="human:protein_1",
                study_id="human",
                study_label="human study",
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
                log2_fold_change=1.2,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="human effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_1",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Stat1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.9,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.7,
                significant=True,
                note="first mouse ortholog effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_2",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_2",
                representative_protein_ref="Q9MOUSE2",
                protein_refs=("Q9MOUSE2",),
                accession_aliases=(),
                gene_symbol="Stat1l",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=-0.8,
                direction=CrossStudyEffectDirection.DOWN,
                p_value=0.003,
                adjusted_p_value=0.03,
                robustness_score=0.72,
                significant=True,
                note="second mouse ortholog effect",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
                source_gene_symbol="STAT1",
                target_gene_symbol="Stat1",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE2",
                source_gene_symbol="STAT1",
                target_gene_symbol="Stat1l",
            ),
        ),
    )

    matched_rows = [
        entry
        for entry in report.comparisons
        if entry.source_study_id == "human" and entry.target_observation_id is not None
    ]

    assert len(matched_rows) == 2
    assert {entry.mapping_cardinality for entry in matched_rows} == {
        OrthologMappingCardinality.ONE_TO_MANY
    }
    assert {entry.ambiguity_status for entry in matched_rows} == {
        CrossSpeciesOrthologAmbiguityStatus.ONE_TO_MANY_ORTHOLOG
    }
    assert {entry.evidence_status for entry in matched_rows} == {
        CrossSpeciesEffectEvidenceStatus.CONSERVED_EFFECT,
        CrossSpeciesEffectEvidenceStatus.DIVERGENT_EFFECT,
    }
    assert all(entry.ambiguous_mapping for entry in matched_rows)
    rendered = render_cross_species_effect_comparison_tsv(report)
    assert "Q9MOUSE1" in rendered
    assert "Q9MOUSE2" in rendered


def test_cross_species_effect_comparison_preserves_many_to_many_ortholog_rows() -> None:
    report = build_cross_species_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="human:protein_5",
                study_id="human",
                study_label="human study",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_5",
                representative_protein_ref="P005",
                protein_refs=("P005",),
                accession_aliases=(),
                gene_symbol="MAPKX",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="human source effect 1",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="human:protein_6",
                study_id="human",
                study_label="human study",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_6",
                representative_protein_ref="P006",
                protein_refs=("P006",),
                accession_aliases=(),
                gene_symbol="MAPKY",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.9,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.79,
                significant=True,
                note="human source effect 2",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_5",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_5",
                representative_protein_ref="M005",
                protein_refs=("M005",),
                accession_aliases=(),
                gene_symbol="Mapkx",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.8,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.003,
                adjusted_p_value=0.03,
                robustness_score=0.7,
                significant=True,
                note="mouse target effect 1",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_6",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_6",
                representative_protein_ref="M006",
                protein_refs=("M006",),
                accession_aliases=(),
                gene_symbol="Mapky",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.7,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.004,
                adjusted_p_value=0.04,
                robustness_score=0.69,
                significant=True,
                note="mouse target effect 2",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P005",
                target_species="Mus musculus",
                target_protein_ref="M005",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P005",
                target_species="Mus musculus",
                target_protein_ref="M006",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P006",
                target_species="Mus musculus",
                target_protein_ref="M005",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P006",
                target_species="Mus musculus",
                target_protein_ref="M006",
            ),
        ),
    )

    matched_rows = [
        entry
        for entry in report.comparisons
        if entry.source_study_id == "human" and entry.target_observation_id is not None
    ]

    assert len(matched_rows) == 4
    assert {entry.mapping_cardinality for entry in matched_rows} == {
        OrthologMappingCardinality.MANY_TO_MANY
    }
    assert {entry.ambiguity_status for entry in matched_rows} == {
        CrossSpeciesOrthologAmbiguityStatus.MANY_TO_MANY_ORTHOLOG
    }
    assert all(
        entry.evidence_status is CrossSpeciesEffectEvidenceStatus.CONSERVED_EFFECT
        for entry in matched_rows
    )


def test_cross_species_effect_comparison_does_not_use_gene_symbol_as_orthology() -> (
    None
):
    report = build_cross_species_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="human:protein_1",
                study_id="human",
                study_label="human study",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="FOXO1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.1,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="human source effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_1",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Foxo1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.75,
                significant=True,
                note="mouse effect without ortholog row",
            ),
        ),
        ortholog_records=(),
    )

    assert report.summary.no_ortholog_relationship_count == 2
    assert all(entry.target_observation_id is None for entry in report.comparisons)
    assert all(
        entry.evidence_status
        is CrossSpeciesEffectEvidenceStatus.NO_ORTHOLOG_RELATIONSHIP
        for entry in report.comparisons
    )


def test_cross_species_effect_comparison_marks_missing_species_studies_unsupported() -> (
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
    )

    report = build_cross_species_effect_comparison_report(
        (
            CrossStudyProteinStudyInput(
                study_id="human_label_free",
                study_result=build_proteomics_study_result(biological_report),
                species="Homo sapiens",
            ),
            CrossStudyProteinStudyInput(
                study_id="tmt_without_species",
                study_result=build_proteomics_study_result(tmt_workflow),
            ),
        ),
        ortholog_records=(),
    )

    assert report.summary.supported_study_count == 1
    assert report.summary.unsupported_study_count == 1
    assert report.comparisons == ()
    assert report.unsupported_studies[0].study_id == "tmt_without_species"
    assert "explicit study species" in report.unsupported_studies[0].reason


def test_cross_species_effect_comparison_marks_heterogeneous_contrasts_explicitly() -> (
    None
):
    report = build_cross_species_effect_comparison_report_from_observations(
        (
            CrossStudyProteinEffectObservation(
                observation_id="human:protein_1",
                study_id="human",
                study_label="human study",
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
                log2_fold_change=1.0,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="human effect",
            ),
            CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_1",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Stat1",
                condition_a="resistant",
                condition_b="sensitive",
                log2_fold_change=0.8,
                direction=CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.7,
                significant=True,
                note="mouse effect",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
            ),
        ),
    )

    matched_row = next(
        entry for entry in report.comparisons if entry.target_observation_id is not None
    )

    assert (
        matched_row.contrast_alignment_status
        is CrossSpeciesEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
    )
    assert (
        matched_row.evidence_status
        is CrossSpeciesEffectEvidenceStatus.HETEROGENEOUS_CONTRASTS
    )
