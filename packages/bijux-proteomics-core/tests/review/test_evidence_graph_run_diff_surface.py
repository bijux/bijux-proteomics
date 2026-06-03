# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
    compare_evidence_graph_runs,
)


def build_run_diff_fixture_graphs() -> tuple[
    ProteomicsEvidenceGraph, ProteomicsEvidenceGraph
]:
    left = ProteomicsEvidenceGraphBuilder()
    right = ProteomicsEvidenceGraphBuilder()

    _add_protein_claim(
        left,
        protein_id="P10001",
        peptide_id="PEPA",
        claim_state="changed",
        row_suffix="10",
    )
    _add_protein_claim(
        right,
        protein_id="P10001",
        peptide_id="PEPA",
        claim_state="changed",
        row_suffix="10",
        shared_only=True,
    )
    _add_protein_claim(
        left,
        protein_id="P20002",
        peptide_id="PEPB",
        claim_state="changed",
        row_suffix="20",
    )
    _add_protein_claim(
        right,
        protein_id="P30003",
        peptide_id="PEPC",
        claim_state="changed",
        row_suffix="30",
    )

    _add_peptide_claim(
        left, peptide_id="PEPDIFF", claim_state="upregulated", row_suffix="40"
    )
    _add_peptide_claim(
        right, peptide_id="PEPDIFF", claim_state="unchanged", row_suffix="40"
    )

    _add_ptm_claim(
        left,
        protein_id="P40004",
        peptide_id="PEPPTM",
        ptm_ref="P40004:S3:Phospho",
        claim_state="changed",
        localization_confidence=0.95,
        row_suffix="50",
    )
    _add_ptm_claim(
        right,
        protein_id="P40004",
        peptide_id="PEPPTM",
        ptm_ref="P40004:S3:Phospho",
        claim_state="changed",
        localization_confidence=0.6,
        row_suffix="50",
    )

    _add_qc_claim(left, run_id="R1", qc_state="accepted", row_suffix="60")
    _add_qc_claim(right, run_id="R1", qc_state="caution", row_suffix="60")

    _add_pathway_claim(
        left,
        protein_id="P50005",
        peptide_id="PEPPATH",
        pathway_id="R-HSA-50005",
        protein_trust_class="high",
        row_suffix="70",
    )
    _add_pathway_claim(
        right,
        protein_id="P50005",
        peptide_id="PEPPATH",
        pathway_id="R-HSA-50005",
        protein_trust_class="single_run_only",
        row_suffix="70",
    )

    return left.build(), right.build()


def test_compare_evidence_graph_runs_reports_scientific_conclusion_changes() -> None:
    left_graph, right_graph = build_run_diff_fixture_graphs()

    report = compare_evidence_graph_runs(left_graph, right_graph)

    assert report.entry_count == 7
    assert report.category_counts == {
        "pathway": 1,
        "peptide": 1,
        "protein": 3,
        "ptm_site": 1,
        "qc_decision": 1,
    }
    assert report.change_counts == {
        "added": 1,
        "changed": 5,
        "removed": 1,
    }

    by_key = {
        (entry.category.value, entry.entity_ref): entry for entry in report.entries
    }
    assert by_key[("protein", "P10001")].change_kind.value == "changed"
    assert by_key[("protein", "P20002")].change_kind.value == "removed"
    assert by_key[("protein", "P30003")].change_kind.value == "added"
    assert by_key[("peptide", "PEPDIFF")].left_claim_state == "upregulated"
    assert by_key[("peptide", "PEPDIFF")].right_claim_state == "unchanged"
    assert (
        by_key[("ptm_site", "P40004:S3:Phospho")].left_evidence_tier
        == "high_confidence"
    )
    assert by_key[("ptm_site", "P40004:S3:Phospho")].right_evidence_tier == "weak"
    assert by_key[("qc_decision", "R1")].left_claim_state == "accepted"
    assert by_key[("qc_decision", "R1")].right_claim_state == "caution"
    assert by_key[("pathway", "R-HSA-50005")].left_evidence_tier == "high_confidence"
    assert by_key[("pathway", "R-HSA-50005")].right_evidence_tier == "weak"


def test_compare_evidence_graph_runs_preserves_row_provenance_for_changed_claims() -> (
    None
):
    left_graph, right_graph = build_run_diff_fixture_graphs()

    report = compare_evidence_graph_runs(left_graph, right_graph)

    peptide_diff = next(
        entry
        for entry in report.entries
        if entry.category.value == "peptide" and entry.entity_ref == "PEPDIFF"
    )
    assert peptide_diff.left_source_row_refs == ("peptide_stats.tsv:40",)
    assert peptide_diff.right_source_row_refs == ("peptide_stats.tsv:40",)


def _add_protein_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    claim_state: str,
    row_suffix: str,
    shared_only: bool = False,
    protein_trust_class: str = "high",
) -> None:
    protein = builder.add_protein(
        protein_id,
        label=protein_id,
        trust_class=protein_trust_class,
    )
    peptide = builder.add_peptide(peptide_id, label=peptide_id, trust_class="high")
    claim = builder.add_statistical_result(
        f"protein:treatment_vs_control:{protein_id}",
        label=f"protein result {protein_id}",
        claim_state=claim_state,
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref=protein_id,
            ),
        ),
    )
    spectrum = builder.add_spectrum(
        f"scan={row_suffix}", label=f"scan={row_suffix}", trust_class="high"
    )
    psm = builder.add_psm(
        f"psm:{row_suffix}", label=f"psm:{row_suffix}", trust_class="high"
    )
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        psm.node_id,
        source_row_ref=f"psm.tsv:{row_suffix}",
        confidence=0.98,
        reason=f"strong spectrum supports psm {row_suffix}",
    )
    builder.add_psm_supports_peptide(
        psm.node_id,
        peptide.node_id,
        source_row_ref=f"peptide.tsv:{row_suffix}",
        confidence=0.97,
        reason=f"accepted psm {row_suffix} supports {peptide_id}",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"protein_matrix.tsv:{row_suffix}",
        confidence=0.95,
        reason=f"{peptide_id} quantifies {protein_id}",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        claim.node_id,
        source_row_ref=f"protein_stats.tsv:{row_suffix}",
        confidence=0.91,
        reason=f"{protein_id} supports final protein result",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"digest.tsv:{row_suffix}",
        confidence=1.0,
        reason=f"{peptide_id} maps to {protein_id}",
    )
    if shared_only:
        alternate = builder.add_protein(
            f"{protein_id}:alt", label=f"{protein_id}:alt", trust_class="high"
        )
        builder.add_peptide_maps_to_protein(
            peptide.node_id,
            alternate.node_id,
            source_row_ref=f"digest.tsv:{row_suffix}a",
            confidence=1.0,
            reason=f"{peptide_id} also maps to alternate protein",
        )


def _add_peptide_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    peptide_id: str,
    claim_state: str,
    row_suffix: str,
) -> None:
    peptide = builder.add_peptide(peptide_id, label=peptide_id, trust_class="high")
    claim = builder.add_statistical_result(
        f"peptide:treatment_vs_control:{peptide_id}",
        label=f"peptide result {peptide_id}",
        claim_state=claim_state,
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PEPTIDE,
                entity_ref=peptide_id,
            ),
        ),
    )
    builder.add_peptide_supports_statistical_result(
        peptide.node_id,
        claim.node_id,
        source_row_ref=f"peptide_stats.tsv:{row_suffix}",
        confidence=0.92,
        reason=f"{peptide_id} supports peptide result",
    )


def _add_ptm_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    ptm_ref: str,
    claim_state: str,
    localization_confidence: float,
    row_suffix: str,
) -> None:
    protein = builder.add_protein(protein_id, label=protein_id, trust_class="high")
    peptide = builder.add_peptide(peptide_id, label=peptide_id, trust_class="high")
    modified = builder.add_modified_peptide(
        f"{peptide_id}[Phospho@S3]",
        label=f"{peptide_id}[Phospho@S3]",
        trust_class="high",
    )
    ptm_site = builder.add_ptm_site(ptm_ref, label=ptm_ref, trust_class="high")
    claim = builder.add_statistical_result(
        f"ptm:treatment_vs_control:{ptm_ref}",
        label=f"ptm result {ptm_ref}",
        claim_state=claim_state,
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PTM_SITE,
                entity_ref=ptm_ref,
            ),
        ),
    )
    spectrum = builder.add_spectrum(
        f"scan={row_suffix}p", label=f"scan={row_suffix}p", trust_class="high"
    )
    psm = builder.add_psm(
        f"psm:{row_suffix}p", label=f"psm:{row_suffix}p", trust_class="high"
    )
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        psm.node_id,
        source_row_ref=f"psm.tsv:{row_suffix}",
        confidence=0.98,
        reason=f"strong spectrum supports ptm psm {row_suffix}",
    )
    builder.add_psm_supports_peptide(
        psm.node_id,
        peptide.node_id,
        source_row_ref=f"peptide.tsv:{row_suffix}",
        confidence=0.97,
        reason=f"accepted psm {row_suffix} supports {peptide_id}",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"protein_matrix.tsv:{row_suffix}",
        confidence=0.95,
        reason=f"{peptide_id} quantifies {protein_id}",
    )
    builder.add_peptide_has_modified_form(
        peptide.node_id,
        modified.node_id,
        source_row_ref=f"ptm.tsv:{row_suffix}",
        confidence=0.92,
        reason=f"{peptide_id} carries phospho form",
    )
    builder.add_modified_peptide_localizes_ptm_site(
        modified.node_id,
        ptm_site.node_id,
        source_row_ref=f"ptm.tsv:{row_suffix}a",
        confidence=localization_confidence,
        reason=f"{ptm_ref} localization confidence is explicit",
    )
    builder.add_ptm_site_belongs_to_protein(
        ptm_site.node_id,
        protein.node_id,
        source_row_ref=f"site_mapping.tsv:{row_suffix}",
        confidence=1.0,
        reason=f"{ptm_ref} belongs to {protein_id}",
    )
    builder.add_ptm_site_supports_statistical_result(
        ptm_site.node_id,
        claim.node_id,
        source_row_ref=f"ptm_stats.tsv:{row_suffix}",
        confidence=0.91,
        reason=f"{ptm_ref} supports final PTM result",
    )


def _add_qc_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    run_id: str,
    qc_state: str,
    row_suffix: str,
) -> None:
    run = builder.add_run(run_id, label=run_id, trust_class="high")
    qc = builder.add_qc_decision(
        f"qc:{run_id}:{qc_state}",
        label=f"QC {qc_state} {run_id}",
        claim_state=qc_state,
        trust_class="high" if qc_state == "accepted" else "medium",
    )
    builder.add_run_governed_by_qc_decision(
        run.node_id,
        qc.node_id,
        source_row_ref=f"qc.tsv:{row_suffix}",
        confidence=1.0,
        reason=f"run {run_id} has qc state {qc_state}",
    )


def _add_pathway_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    pathway_id: str,
    protein_trust_class: str,
    row_suffix: str,
) -> None:
    protein = builder.add_protein(
        protein_id, label=protein_id, trust_class=protein_trust_class
    )
    peptide = builder.add_peptide(peptide_id, label=peptide_id, trust_class="high")
    spectrum = builder.add_spectrum(
        f"scan={row_suffix}p", label=f"scan={row_suffix}p", trust_class="high"
    )
    psm = builder.add_psm(
        f"psm:{row_suffix}p", label=f"psm:{row_suffix}p", trust_class="high"
    )
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        psm.node_id,
        source_row_ref=f"psm.tsv:{row_suffix}",
        confidence=0.98,
        reason=f"strong spectrum supports pathway psm {row_suffix}",
    )
    builder.add_psm_supports_peptide(
        psm.node_id,
        peptide.node_id,
        source_row_ref=f"peptide.tsv:{row_suffix}",
        confidence=0.97,
        reason=f"accepted psm {row_suffix} supports {peptide_id}",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"protein_matrix.tsv:{row_suffix}",
        confidence=0.95,
        reason=f"{peptide_id} quantifies {protein_id}",
    )
    pathway = builder.add_pathway(pathway_id, label=pathway_id, trust_class="high")
    claim = builder.add_statistical_result(
        f"pathway:treatment_vs_control:{pathway_id}",
        label=f"pathway result {pathway_id}",
        claim_state="enriched",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PATHWAY,
                entity_ref=pathway_id,
            ),
        ),
    )
    builder.add_protein_member_of_pathway(
        protein.node_id,
        pathway.node_id,
        source_row_ref=f"pathway.tsv:{row_suffix}",
        confidence=0.91,
        reason=f"{protein_id} supports pathway {pathway_id}",
    )
    builder.add_pathway_supports_statistical_result(
        pathway.node_id,
        claim.node_id,
        source_row_ref=f"pathway_stats.tsv:{row_suffix}",
        confidence=0.93,
        reason=f"{pathway_id} is enriched",
    )
