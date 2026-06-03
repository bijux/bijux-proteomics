# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
    detect_evidence_graph_contradictions,
)


def build_contradiction_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    protein = builder.add_protein("P11111", label="P11111")
    peptide_a = builder.add_peptide("PEPA", label="PEPA")
    peptide_b = builder.add_peptide("PEPB", label="PEPB")
    pathway = builder.add_pathway("R-HSA-199420", label="Apoptosis")
    weak_protein_a = builder.add_protein("Q22222", label="Q22222", trust_class="low")
    weak_protein_b = builder.add_protein("Q33333", label="Q33333", trust_class="low")
    ptm_site = builder.add_ptm_site("P11111:S3:Phospho", label="P11111:S3:Phospho")

    protein_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein differential result",
        claim_state="unchanged",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P11111",
            ),
        ),
    )
    peptide_a_result = builder.add_statistical_result(
        "peptide:treatment_vs_control:PEPA",
        label="peptide PEPA differential result",
        claim_state="upregulated",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PEPTIDE,
                entity_ref="PEPA",
            ),
        ),
    )
    peptide_b_result = builder.add_statistical_result(
        "peptide:treatment_vs_control:PEPB",
        label="peptide PEPB differential result",
        claim_state="downregulated",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PEPTIDE,
                entity_ref="PEPB",
            ),
        ),
    )
    ptm_result = builder.add_statistical_result(
        "ptm:treatment_vs_control:P11111:S3:Phospho",
        label="PTM differential result",
        claim_state="upregulated",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PTM_SITE,
                entity_ref="P11111:S3:Phospho",
            ),
        ),
    )
    protein_directional_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111:directional",
        label="protein directional differential result",
        claim_state="upregulated",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P11111",
            ),
        ),
    )
    pathway_result = builder.add_statistical_result(
        "pathway:treatment_vs_control:R-HSA-199420",
        label="pathway enrichment result",
        claim_state="enriched",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PATHWAY,
                entity_ref="R-HSA-199420",
            ),
        ),
    )

    builder.add_peptide_quantifies_protein(
        peptide_a.node_id,
        protein.node_id,
        source_row_ref="features.tsv:10",
        confidence=0.88,
        reason="PEPA contributes to protein quantification",
    )
    builder.add_peptide_quantifies_protein(
        peptide_b.node_id,
        protein.node_id,
        source_row_ref="features.tsv:11",
        confidence=0.87,
        reason="PEPB contributes to protein quantification",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        protein_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.9,
        reason="protein P11111 is unchanged in treatment vs control",
    )
    builder.add_peptide_supports_statistical_result(
        peptide_a.node_id,
        peptide_a_result.node_id,
        source_row_ref="peptide_stats.tsv:4",
        confidence=0.84,
        reason="peptide PEPA is upregulated in treatment vs control",
    )
    builder.add_peptide_supports_statistical_result(
        peptide_b.node_id,
        peptide_b_result.node_id,
        source_row_ref="peptide_stats.tsv:5",
        confidence=0.83,
        reason="peptide PEPB is downregulated in treatment vs control",
    )

    builder.add_ptm_site_belongs_to_protein(
        ptm_site.node_id,
        protein.node_id,
        source_row_ref="site_mapping.tsv:3",
        confidence=1.0,
        reason="PTM site belongs to protein P11111",
    )
    builder.add_ptm_site_supports_statistical_result(
        ptm_site.node_id,
        ptm_result.node_id,
        source_row_ref="ptm_stats.tsv:6",
        confidence=0.9,
        reason="PTM site is upregulated in treatment vs control",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        protein_directional_result.node_id,
        source_row_ref="protein_stats.tsv:5",
        confidence=0.88,
        reason="protein P11111 is upregulated in treatment vs control",
    )

    builder.add_protein_member_of_pathway(
        weak_protein_a.node_id,
        pathway.node_id,
        source_row_ref="pathway.tsv:11",
        confidence=0.7,
        reason="Q22222 is annotated to apoptosis",
    )
    builder.add_protein_member_of_pathway(
        weak_protein_b.node_id,
        pathway.node_id,
        source_row_ref="pathway.tsv:12",
        confidence=0.71,
        reason="Q33333 is annotated to apoptosis",
    )
    builder.add_pathway_supports_statistical_result(
        pathway.node_id,
        pathway_result.node_id,
        source_row_ref="pathway_stats.tsv:3",
        confidence=0.8,
        reason="apoptosis enrichment is significant",
    )
    return builder.build()


def test_detect_evidence_graph_contradictions_finds_backlog_example_patterns() -> None:
    report = detect_evidence_graph_contradictions(build_contradiction_fixture_graph())

    assert report.contradiction_count == 3
    assert report.kind_counts == {
        "pathway_enrichment_with_weak_proteins": 1,
        "protein_unchanged_with_changed_peptides": 1,
        "ptm_change_explained_by_protein": 1,
    }
    kinds = {entry.kind.value for entry in report.entries}
    assert "protein_unchanged_with_changed_peptides" in kinds
    assert "ptm_change_explained_by_protein" in kinds
    assert "pathway_enrichment_with_weak_proteins" in kinds
    assert any(
        "protein_stats.tsv:4" in entry.source_row_refs for entry in report.entries
    )
    entries_by_kind = {entry.kind.value: entry for entry in report.entries}
    assert (
        entries_by_kind["protein_unchanged_with_changed_peptides"].severity.value
        == "fail"
    )
    assert entries_by_kind[
        "protein_unchanged_with_changed_peptides"
    ].source_row_refs == (
        "peptide_stats.tsv:4",
        "peptide_stats.tsv:5",
        "protein_stats.tsv:4",
    )
    assert (
        entries_by_kind["ptm_change_explained_by_protein"].severity.value == "caution"
    )
    assert entries_by_kind["ptm_change_explained_by_protein"].source_row_refs == (
        "protein_stats.tsv:5",
        "ptm_stats.tsv:6",
    )
    assert (
        entries_by_kind["pathway_enrichment_with_weak_proteins"].severity.value
        == "fail"
    )
    assert entries_by_kind["pathway_enrichment_with_weak_proteins"].source_row_refs == (
        "pathway.tsv:11",
        "pathway.tsv:12",
        "pathway_stats.tsv:3",
    )


def test_detect_evidence_graph_contradictions_skips_pathway_when_support_is_not_uniformly_weak() -> (
    None
):
    builder = ProteomicsEvidenceGraphBuilder()
    pathway = builder.add_pathway("R-HSA-199420", label="Apoptosis")
    weak_protein = builder.add_protein("Q22222", label="Q22222", trust_class="low")
    strong_protein = builder.add_protein("Q33333", label="Q33333", trust_class="high")
    pathway_result = builder.add_statistical_result(
        "pathway:treatment_vs_control:R-HSA-199420",
        label="pathway enrichment result",
        claim_state="enriched",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PATHWAY,
                entity_ref="R-HSA-199420",
            ),
        ),
    )
    builder.add_protein_member_of_pathway(
        weak_protein.node_id,
        pathway.node_id,
        source_row_ref="pathway.tsv:11",
        confidence=0.7,
        reason="Q22222 is annotated to apoptosis",
    )
    builder.add_protein_member_of_pathway(
        strong_protein.node_id,
        pathway.node_id,
        source_row_ref="pathway.tsv:12",
        confidence=0.91,
        reason="Q33333 is annotated to apoptosis",
    )
    builder.add_pathway_supports_statistical_result(
        pathway.node_id,
        pathway_result.node_id,
        source_row_ref="pathway_stats.tsv:3",
        confidence=0.8,
        reason="apoptosis enrichment is significant",
    )

    report = detect_evidence_graph_contradictions(builder.build())

    assert report.contradiction_count == 0
    assert report.entries == ()
