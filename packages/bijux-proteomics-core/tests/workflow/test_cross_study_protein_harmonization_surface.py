# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    build_proteomics_study_result,
    build_tmt_experiment_workflow_bundle,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinMatchBasis,
    CrossStudyProteinObservation,
    CrossStudyProteinObservationSourceKind,
    CrossStudyProteinStudyInput,
    CrossStudyProteinUnresolvedReason,
    build_cross_study_protein_harmonization_report_from_observations,
    extract_cross_study_protein_observations,
    render_cross_study_protein_harmonization_tsv,
    render_cross_study_protein_unresolved_tsv,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_extract_cross_study_protein_observations_preserves_biological_and_tmt_surfaces() -> (
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

    extraction = extract_cross_study_protein_observations(
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
    assert any(
        entry.source_kind
        is CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD
        for entry in extraction.observations
    )
    assert any(
        entry.source_kind
        is CrossStudyProteinObservationSourceKind.LABEL_BASED_DIFFERENTIAL_ROW
        for entry in extraction.observations
    )


def test_cross_study_protein_harmonization_keeps_gene_symbol_only_matches_unresolved() -> (
    None
):
    report = build_cross_study_protein_harmonization_report_from_observations(
        (
            CrossStudyProteinObservation(
                observation_id="study_a:protein_a",
                study_id="study_a",
                study_label="human cohort a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_a",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT3",
                note="first study protein card",
            ),
            CrossStudyProteinObservation(
                observation_id="study_b:protein_b",
                study_id="study_b",
                study_label="human cohort b",
                study_kind=ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_b",
                representative_protein_ref="Q22222",
                protein_refs=("Q22222",),
                accession_aliases=(),
                gene_symbol="STAT3",
                note="second study protein card",
            ),
        )
    )

    assert report.harmonized_entries == ()
    assert len(report.unresolved_entries) == 2
    assert {entry.reason for entry in report.unresolved_entries} == {
        CrossStudyProteinUnresolvedReason.GENE_SYMBOL_ONLY_MATCH
    }
    assert report.summary.gene_symbol_only_unresolved_count == 2
    assert "gene_symbol_only_match" in render_cross_study_protein_unresolved_tsv(report)


def test_cross_study_protein_harmonization_links_exact_and_unique_ortholog_support() -> (
    None
):
    report = build_cross_study_protein_harmonization_report_from_observations(
        (
            CrossStudyProteinObservation(
                observation_id="human_a:card_1",
                study_id="human_a",
                study_label="human study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=("P11111-2",),
                gene_symbol="MAPK1",
                note="human card",
            ),
            CrossStudyProteinObservation(
                observation_id="human_b:card_2",
                study_id="human_b",
                study_label="human study b",
                study_kind=ProteomicsStudyKind.MAXQUANT,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_2",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="MAPK1",
                note="human alias-backed card",
            ),
            CrossStudyProteinObservation(
                observation_id="mouse_c:card_3",
                study_id="mouse_c",
                study_label="mouse study c",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_3",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Mapk1",
                note="mouse ortholog-backed card",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
                source_gene_symbol="MAPK1",
                target_gene_symbol="Mapk1",
            ),
        ),
    )

    assert len(report.harmonized_entries) == 3
    assert report.unresolved_entries == ()
    assert report.summary.harmonized_group_count == 1
    assert report.summary.ortholog_linked_group_count == 1
    assert {entry.match_basis for entry in report.harmonized_entries} == {
        CrossStudyProteinMatchBasis.EXACT_ACCESSION_AND_UNIQUE_ORTHOLOG
    }
    assert "harmonized_protein_001" in render_cross_study_protein_harmonization_tsv(
        report
    )


def test_cross_study_protein_harmonization_keeps_one_to_many_orthologs_ambiguous() -> (
    None
):
    report = build_cross_study_protein_harmonization_report_from_observations(
        (
            CrossStudyProteinObservation(
                observation_id="human:card_1",
                study_id="human",
                study_label="human study",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="FOXO1",
                note="human source protein",
            ),
            CrossStudyProteinObservation(
                observation_id="mouse:card_2",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_2",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Foxo1",
                note="first mouse ortholog candidate",
            ),
            CrossStudyProteinObservation(
                observation_id="mouse:card_3",
                study_id="mouse",
                study_label="mouse study",
                study_kind=ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_3",
                representative_protein_ref="Q9MOUSE2",
                protein_refs=("Q9MOUSE2",),
                accession_aliases=(),
                gene_symbol="Foxo1",
                note="second mouse ortholog candidate",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
                source_gene_symbol="FOXO1",
                target_gene_symbol="Foxo1",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE2",
                source_gene_symbol="FOXO1",
                target_gene_symbol="Foxo1",
            ),
        ),
    )

    assert report.harmonized_entries == ()
    assert len(report.unresolved_entries) == 3
    assert {entry.reason for entry in report.unresolved_entries} == {
        CrossStudyProteinUnresolvedReason.AMBIGUOUS_ORTHOLOG_MAPPING
    }
    assert report.summary.ambiguous_ortholog_entry_count == 3
    human_entry = next(
        entry for entry in report.unresolved_entries if entry.study_id == "human"
    )
    assert set(human_entry.candidate_observation_ids) == {
        "mouse:card_2",
        "mouse:card_3",
    }
