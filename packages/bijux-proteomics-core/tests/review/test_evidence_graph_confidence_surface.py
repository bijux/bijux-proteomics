# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.chromatographic_evidence import (
    ChromatographicEvidenceScoreReport,
    ChromatographicPeptideEvidenceEntry,
)
from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
    propagate_evidence_graph_confidence,
)


def build_confidence_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    strong_spectrum = builder.add_spectrum("scan=1001", label="scan=1001", trust_class="high")
    weak_spectrum = builder.add_spectrum("scan=1002", label="scan=1002", trust_class="low")
    strong_psm = builder.add_psm("psm:1001", label="psm:1001", trust_class="high")
    weak_psm = builder.add_psm("psm:1002", label="psm:1002", trust_class="low")
    strong_peptide = builder.add_peptide("PEPA", label="PEPA", trust_class="high")
    weak_peptide = builder.add_peptide("PEPB", label="PEPB", trust_class="low")
    strong_protein = builder.add_protein("P11111", label="P11111", trust_class="high")
    weak_protein = builder.add_protein("P22222", label="P22222", trust_class="low")
    modified_peptide = builder.add_modified_peptide(
        "PEPA[Phospho@S3]",
        label="PEPA[Phospho@S3]",
        trust_class="high",
    )
    ptm_site = builder.add_ptm_site(
        "P11111:S3:Phospho",
        label="P11111:S3:Phospho",
        trust_class="high",
    )
    strong_pathway = builder.add_pathway(
        "R-HSA-199420",
        label="Apoptosis",
        trust_class="high",
    )
    weak_pathway = builder.add_pathway(
        "R-HSA-6802957",
        label="Signaling by weak support",
        trust_class="low",
    )

    strong_protein_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="strong protein result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P11111",
            ),
        ),
    )
    weak_protein_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P22222",
        label="weak protein result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P22222",
            ),
        ),
    )
    ptm_result = builder.add_statistical_result(
        "ptm:treatment_vs_control:P11111:S3:Phospho",
        label="ptm site result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PTM_SITE,
                entity_ref="P11111:S3:Phospho",
            ),
        ),
    )
    strong_pathway_result = builder.add_statistical_result(
        "pathway:treatment_vs_control:R-HSA-199420",
        label="strong pathway result",
        claim_state="enriched",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PATHWAY,
                entity_ref="R-HSA-199420",
            ),
        ),
    )
    weak_pathway_result = builder.add_statistical_result(
        "pathway:treatment_vs_control:R-HSA-6802957",
        label="weak pathway result",
        claim_state="enriched",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PATHWAY,
                entity_ref="R-HSA-6802957",
            ),
        ),
    )

    builder.add_spectrum_supports_psm(
        strong_spectrum.node_id,
        strong_psm.node_id,
        source_row_ref="psm.tsv:4",
        confidence=0.97,
        reason="strong spectrum supports accepted PSM",
    )
    builder.add_spectrum_supports_psm(
        weak_spectrum.node_id,
        weak_psm.node_id,
        source_row_ref="psm.tsv:5",
        confidence=0.28,
        reason="weak spectrum supports low-confidence PSM",
    )
    builder.add_psm_supports_peptide(
        strong_psm.node_id,
        strong_peptide.node_id,
        source_row_ref="peptide.tsv:4",
        confidence=0.96,
        reason="strong PSM supports peptide PEPA",
    )
    builder.add_psm_supports_peptide(
        weak_psm.node_id,
        weak_peptide.node_id,
        source_row_ref="peptide.tsv:5",
        confidence=0.32,
        reason="weak PSM supports peptide PEPB",
    )
    builder.add_peptide_quantifies_protein(
        strong_peptide.node_id,
        strong_protein.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.93,
        reason="strong peptide quantifies protein P11111",
    )
    builder.add_peptide_quantifies_protein(
        weak_peptide.node_id,
        weak_protein.node_id,
        source_row_ref="protein_matrix.tsv:5",
        confidence=0.35,
        reason="weak peptide quantifies protein P22222",
    )
    builder.add_protein_supports_statistical_result(
        strong_protein.node_id,
        strong_protein_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.91,
        reason="strong protein differential result",
    )
    builder.add_protein_supports_statistical_result(
        weak_protein.node_id,
        weak_protein_result.node_id,
        source_row_ref="protein_stats.tsv:5",
        confidence=0.91,
        reason="weak protein differential result shares final statistic confidence",
    )

    builder.add_peptide_has_modified_form(
        strong_peptide.node_id,
        modified_peptide.node_id,
        source_row_ref="ptm.tsv:4",
        confidence=0.92,
        reason="strong peptide carries phospho form",
    )
    builder.add_modified_peptide_localizes_ptm_site(
        modified_peptide.node_id,
        ptm_site.node_id,
        source_row_ref="ptm.tsv:4",
        confidence=0.94,
        reason="modified peptide localizes phospho site",
    )
    builder.add_ptm_site_belongs_to_protein(
        ptm_site.node_id,
        strong_protein.node_id,
        source_row_ref="site_mapping.tsv:3",
        confidence=1.0,
        reason="PTM site belongs to protein P11111",
    )
    builder.add_ptm_site_supports_statistical_result(
        ptm_site.node_id,
        ptm_result.node_id,
        source_row_ref="ptm_stats.tsv:6",
        confidence=0.9,
        reason="PTM site differential result",
    )

    builder.add_protein_member_of_pathway(
        strong_protein.node_id,
        strong_pathway.node_id,
        source_row_ref="pathway.tsv:10",
        confidence=0.89,
        reason="strong protein supports pathway membership",
    )
    builder.add_protein_member_of_pathway(
        weak_protein.node_id,
        weak_pathway.node_id,
        source_row_ref="pathway.tsv:11",
        confidence=0.42,
        reason="weak protein supports pathway membership",
    )
    builder.add_pathway_supports_statistical_result(
        strong_pathway.node_id,
        strong_pathway_result.node_id,
        source_row_ref="pathway_stats.tsv:4",
        confidence=0.92,
        reason="strong pathway enrichment result",
    )
    builder.add_pathway_supports_statistical_result(
        weak_pathway.node_id,
        weak_pathway_result.node_id,
        source_row_ref="pathway_stats.tsv:5",
        confidence=0.92,
        reason="weak pathway enrichment result shares final statistic confidence",
    )
    return builder.build()


def test_propagate_evidence_graph_confidence_depends_on_upstream_quality() -> None:
    report = propagate_evidence_graph_confidence(build_confidence_fixture_graph())

    assert report.entry_count == 5
    assert len(report.tier_counts) > 1

    by_claim = {entry.claim_node_ref: entry for entry in report.entries}
    assert by_claim["protein:treatment_vs_control:P11111"].confidence_tier.value == "high"
    assert by_claim["protein:treatment_vs_control:P22222"].confidence_tier.value == "low"
    assert (
        by_claim["protein:treatment_vs_control:P11111"].propagated_score
        > by_claim["protein:treatment_vs_control:P22222"].propagated_score
    )
    assert by_claim["ptm:treatment_vs_control:P11111:S3:Phospho"].confidence_tier.value == "high"
    assert by_claim["pathway:treatment_vs_control:R-HSA-199420"].confidence_tier.value == "high"
    assert by_claim["pathway:treatment_vs_control:R-HSA-6802957"].confidence_tier.value == "low"


def test_propagate_evidence_graph_confidence_preserves_upstream_provenance() -> None:
    report = propagate_evidence_graph_confidence(build_confidence_fixture_graph())

    protein_entry = next(
        entry
        for entry in report.entries
        if entry.claim_node_ref == "protein:treatment_vs_control:P11111"
    )
    assert "protein:protein:P11111" not in protein_entry.upstream_node_ids
    assert "psm:psm:1001" in protein_entry.upstream_node_ids
    assert "spectrum:scan=1001" in protein_entry.upstream_node_ids
    assert protein_entry.source_row_refs == (
        "peptide.tsv:4",
        "protein_matrix.tsv:4",
        "protein_stats.tsv:4",
        "psm.tsv:4",
    )


def test_propagate_evidence_graph_confidence_absorbs_chromatographic_peptide_scores() -> None:
    builder = ProteomicsEvidenceGraphBuilder()

    spectrum_a = builder.add_spectrum("scan=2001", label="scan=2001", trust_class="high")
    spectrum_b = builder.add_spectrum("scan=2002", label="scan=2002", trust_class="high")
    psm_a = builder.add_psm("psm:2001", label="psm:2001", trust_class="high")
    psm_b = builder.add_psm("psm:2002", label="psm:2002", trust_class="high")
    peptide_a = builder.add_peptide("PEPA", label="PEPA", trust_class="high")
    peptide_b = builder.add_peptide("PEPB", label="PEPB", trust_class="high")
    protein_a = builder.add_protein("P30001", label="P30001", trust_class="high")
    protein_b = builder.add_protein("P30002", label="P30002", trust_class="high")
    result_a = builder.add_statistical_result(
        "protein:treatment_vs_control:P30001",
        label="protein A differential result",
        claim_state="changed",
    )
    result_b = builder.add_statistical_result(
        "protein:treatment_vs_control:P30002",
        label="protein B differential result",
        claim_state="changed",
    )

    for spectrum, psm, peptide, protein, result, row_number in (
        (spectrum_a, psm_a, peptide_a, protein_a, result_a, 21),
        (spectrum_b, psm_b, peptide_b, protein_b, result_b, 22),
    ):
        builder.add_spectrum_supports_psm(
            spectrum.node_id,
            psm.node_id,
            source_row_ref=f"psm.tsv:{row_number}",
            confidence=0.95,
            reason="matched spectrum supports accepted PSM",
        )
        builder.add_psm_supports_peptide(
            psm.node_id,
            peptide.node_id,
            source_row_ref=f"peptide.tsv:{row_number}",
            confidence=0.95,
            reason="accepted PSM supports peptide sequence",
        )
        builder.add_peptide_quantifies_protein(
            peptide.node_id,
            protein.node_id,
            source_row_ref=f"protein_matrix.tsv:{row_number}",
            confidence=0.95,
            reason="accepted peptide quantifies target protein",
        )
        builder.add_protein_supports_statistical_result(
            protein.node_id,
            result.node_id,
            source_row_ref=f"protein_stats.tsv:{row_number}",
            confidence=0.95,
            reason="accepted protein supports final differential result",
        )

    graph = builder.build()
    baseline = propagate_evidence_graph_confidence(graph)
    chromatographic = propagate_evidence_graph_confidence(
        graph,
        chromatographic_score_report=ChromatographicEvidenceScoreReport(
            run_ids=("run_a", "run_b"),
            peptide_entries=(
                ChromatographicPeptideEvidenceEntry(
                    peptide_ref="PEPA",
                    target_ids=("anchor_alpha",),
                    total_run_count=2,
                    detected_run_count=2,
                    peak_shape_score=1.0,
                    apex_intensity_score=1.0,
                    signal_to_noise_score=1.0,
                    rt_agreement_score=1.0,
                    missingness_score=1.0,
                    chromatographic_evidence_score=1.0,
                ),
                ChromatographicPeptideEvidenceEntry(
                    peptide_ref="PEPB",
                    target_ids=("anchor_beta",),
                    total_run_count=2,
                    detected_run_count=1,
                    peak_shape_score=0.45,
                    apex_intensity_score=0.35,
                    signal_to_noise_score=0.30,
                    rt_agreement_score=0.0,
                    missingness_score=0.5,
                    chromatographic_evidence_score=0.32,
                    concern_codes=("missing_peak", "rt_outside_tolerance"),
                ),
            ),
        ),
    )

    baseline_by_claim = {entry.claim_node_ref: entry for entry in baseline.entries}
    chromatographic_by_claim = {
        entry.claim_node_ref: entry for entry in chromatographic.entries
    }

    assert (
        baseline_by_claim["protein:treatment_vs_control:P30001"].propagated_score
        == baseline_by_claim["protein:treatment_vs_control:P30002"].propagated_score
    )
    assert (
        chromatographic_by_claim["protein:treatment_vs_control:P30001"].propagated_score
        > chromatographic_by_claim["protein:treatment_vs_control:P30002"].propagated_score
    )
    assert (
        chromatographic_by_claim["protein:treatment_vs_control:P30001"].confidence_tier.value
        == "high"
    )
    assert (
        chromatographic_by_claim["protein:treatment_vs_control:P30002"].confidence_tier.value
        == "moderate"
    )
    assert "peptide chromatographic evidence" in chromatographic_by_claim[
        "protein:treatment_vs_control:P30001"
    ].rationale
