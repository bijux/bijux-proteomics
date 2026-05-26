# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
    build_evidence_graph_final_result_table,
)

from .test_evidence_graph_contradiction_surface import build_contradiction_fixture_graph


def build_downgrade_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    clean = _add_clean_protein_claim(
        builder,
        protein_id="P10001",
        peptide_id="PEPCLEAN",
        claim_ref="protein:treatment_vs_control:P10001",
        row_suffix="10",
    )
    shared = _add_shared_only_protein_claim(
        builder,
        protein_id="P10002",
        alternate_protein_id="P90002",
        peptide_id="PEPSHARED",
        claim_ref="protein:treatment_vs_control:P10002",
        row_suffix="20",
    )
    contaminant = _add_contaminant_overlap_protein_claim(
        builder,
        protein_id="P10003",
        contaminant_id="CONTAM10003",
        peptide_id="PEPCONTAM",
        claim_ref="protein:treatment_vs_control:P10003",
        row_suffix="30",
    )
    poor_qc = _add_poor_qc_protein_claim(
        builder,
        protein_id="P10004",
        peptide_id="PEPQC",
        claim_ref="protein:treatment_vs_control:P10004",
        row_suffix="40",
    )
    imputed = _add_imputed_protein_claim(
        builder,
        protein_id="P10005",
        peptide_id="PEPIMP",
        claim_ref="protein:treatment_vs_control:P10005",
        row_suffix="50",
    )
    ptm = _add_low_localization_ptm_claim(
        builder,
        protein_id="P10006",
        peptide_id="PEPPTM",
        ptm_ref="P10006:S3:Phospho",
        claim_ref="ptm:treatment_vs_control:P10006:S3:Phospho",
        row_suffix="60",
    )
    pathway = _add_poor_reproducibility_pathway_claim(
        builder,
        protein_id="P10007",
        peptide_id="PEPPATH",
        pathway_id="R-HSA-10007",
        claim_ref="pathway:treatment_vs_control:R-HSA-10007",
        row_suffix="70",
    )

    assert clean
    assert shared
    assert contaminant
    assert poor_qc
    assert imputed
    assert ptm
    assert pathway
    return builder.build()


def test_build_evidence_graph_final_result_table_applies_graph_downgrade_rules() -> None:
    report = build_evidence_graph_final_result_table(build_downgrade_fixture_graph())

    assert report.entry_count == 7
    by_claim = {entry.claim_node_ref: entry for entry in report.entries}

    assert by_claim["protein:treatment_vs_control:P10001"].evidence_tier.value == "high_confidence"
    assert by_claim["protein:treatment_vs_control:P10001"].downgrade_reasons == ()

    assert by_claim["protein:treatment_vs_control:P10002"].evidence_tier.value == "ambiguous"
    assert [reason.value for reason in by_claim["protein:treatment_vs_control:P10002"].downgrade_reasons] == [
        "shared_peptide_only"
    ]

    assert by_claim["protein:treatment_vs_control:P10003"].evidence_tier.value == "moderate"
    assert [reason.value for reason in by_claim["protein:treatment_vs_control:P10003"].downgrade_reasons] == [
        "contaminant_overlap"
    ]

    assert by_claim["protein:treatment_vs_control:P10004"].evidence_tier.value == "moderate"
    assert [reason.value for reason in by_claim["protein:treatment_vs_control:P10004"].downgrade_reasons] == [
        "poor_run_qc"
    ]

    assert by_claim["protein:treatment_vs_control:P10005"].evidence_tier.value == "moderate"
    assert [reason.value for reason in by_claim["protein:treatment_vs_control:P10005"].downgrade_reasons] == [
        "imputation_dependence"
    ]

    assert by_claim["ptm:treatment_vs_control:P10006:S3:Phospho"].evidence_tier.value == "weak"
    assert [reason.value for reason in by_claim["ptm:treatment_vs_control:P10006:S3:Phospho"].downgrade_reasons] == [
        "low_localization"
    ]

    assert by_claim["pathway:treatment_vs_control:R-HSA-10007"].evidence_tier.value == "weak"
    assert [reason.value for reason in by_claim["pathway:treatment_vs_control:R-HSA-10007"].downgrade_reasons] == [
        "poor_reproducibility"
    ]


def test_build_evidence_graph_final_result_table_preserves_final_result_provenance() -> None:
    report = build_evidence_graph_final_result_table(build_downgrade_fixture_graph())

    imputed = next(
        entry
        for entry in report.entries
        if entry.claim_node_ref == "protein:treatment_vs_control:P10005"
    )
    assert imputed.source_row_refs == (
        "peptide.tsv:50",
        "protein_matrix.tsv:50",
        "protein_stats.tsv:50",
        "psm.tsv:50",
        "quant_stats.tsv:50",
    )


def test_build_evidence_graph_final_result_table_downgrades_fail_contradictions_to_low_confidence() -> None:
    report = build_evidence_graph_final_result_table(build_contradiction_fixture_graph())

    by_claim = {entry.claim_node_ref: entry for entry in report.entries}
    protein_entry = by_claim["protein:treatment_vs_control:P11111"]
    pathway_entry = by_claim["pathway:treatment_vs_control:R-HSA-199420"]

    assert protein_entry.confidence_tier.value == "low"
    assert protein_entry.evidence_tier.value == "weak"
    assert [reason.value for reason in protein_entry.downgrade_reasons] == [
        "severe_contradiction"
    ]

    assert pathway_entry.confidence_tier.value == "low"
    assert pathway_entry.evidence_tier.value == "weak"
    assert [reason.value for reason in pathway_entry.downgrade_reasons] == [
        "severe_contradiction"
    ]


def test_build_evidence_graph_final_result_table_marks_caution_contradictions_without_hiding_claims() -> None:
    report = build_evidence_graph_final_result_table(build_contradiction_fixture_graph())

    by_claim = {entry.claim_node_ref: entry for entry in report.entries}
    ptm_entry = by_claim["ptm:treatment_vs_control:P11111:S3:Phospho"]

    assert ptm_entry.confidence_tier.value == "moderate"
    assert ptm_entry.evidence_tier.value == "weak"
    assert [reason.value for reason in ptm_entry.downgrade_reasons] == [
        "contradiction_caution"
    ]


def _add_clean_protein_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=claim_ref,
        row_suffix=row_suffix,
    )
    return True


def _add_shared_only_protein_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    alternate_protein_id: str,
    peptide_id: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    protein, peptide, _claim = _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=claim_ref,
        row_suffix=row_suffix,
    )
    alternate = builder.add_protein(alternate_protein_id, label=alternate_protein_id, trust_class="high")
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        alternate.node_id,
        source_row_ref=f"digest.tsv:{row_suffix}",
        confidence=1.0,
        reason=f"{peptide_id} also maps to {alternate_protein_id}",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"digest.tsv:{row_suffix}a",
        confidence=1.0,
        reason=f"{peptide_id} maps to {protein_id}",
    )
    return True


def _add_contaminant_overlap_protein_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    contaminant_id: str,
    peptide_id: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    protein, peptide, _claim = _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=claim_ref,
        row_suffix=row_suffix,
    )
    contaminant = builder.add_protein(
        contaminant_id,
        label=contaminant_id,
        trust_class="contaminant",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"digest.tsv:{row_suffix}",
        confidence=1.0,
        reason=f"{peptide_id} maps to {protein_id}",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        contaminant.node_id,
        source_row_ref=f"digest.tsv:{row_suffix}a",
        confidence=0.95,
        reason=f"{peptide_id} also overlaps contaminant {contaminant_id}",
    )
    unique_peptide = builder.add_peptide(f"{peptide_id}U", label=f"{peptide_id}U", trust_class="high")
    unique_spectrum = builder.add_spectrum(
        f"scan={row_suffix}u",
        label=f"scan={row_suffix}u",
        trust_class="high",
    )
    unique_psm = builder.add_psm(f"psm:{row_suffix}u", label=f"psm:{row_suffix}u", trust_class="high")
    builder.add_spectrum_supports_psm(
        unique_spectrum.node_id,
        unique_psm.node_id,
        source_row_ref=f"psm.tsv:{row_suffix}u",
        confidence=0.98,
        reason=f"strong spectrum supports unique psm {row_suffix}u",
    )
    builder.add_psm_supports_peptide(
        unique_psm.node_id,
        unique_peptide.node_id,
        source_row_ref=f"peptide.tsv:{row_suffix}u",
        confidence=0.97,
        reason=f"accepted unique psm {row_suffix}u supports {peptide_id}U",
    )
    builder.add_peptide_quantifies_protein(
        unique_peptide.node_id,
        protein.node_id,
        source_row_ref=f"protein_matrix.tsv:{row_suffix}u",
        confidence=0.94,
        reason=f"{peptide_id}U quantifies {protein_id}",
    )
    builder.add_peptide_maps_to_protein(
        unique_peptide.node_id,
        protein.node_id,
        source_row_ref=f"digest.tsv:{row_suffix}u",
        confidence=1.0,
        reason=f"{peptide_id}U maps uniquely to {protein_id}",
    )
    return True


def _add_poor_qc_protein_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    protein, peptide, _claim = _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=claim_ref,
        row_suffix=row_suffix,
        with_run=True,
    )
    run = builder.add_run(f"R{row_suffix}", label=f"R{row_suffix}", trust_class="high")
    spectrum = builder.add_spectrum(f"scan={row_suffix}", label=f"scan={row_suffix}", trust_class="high")
    psm = builder.add_psm(f"psm:{row_suffix}", label=f"psm:{row_suffix}", trust_class="high")
    qc = builder.add_qc_decision(
        f"qc:R{row_suffix}:caution",
        label=f"QC caution R{row_suffix}",
        claim_state="caution",
        trust_class="medium",
    )
    builder.add_run_acquired_spectrum(
        run.node_id,
        spectrum.node_id,
        source_row_ref=f"spectra.mgf:{row_suffix}",
        confidence=1.0,
        reason=f"run R{row_suffix} acquired scan={row_suffix}",
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
    builder.add_run_governed_by_qc_decision(
        run.node_id,
        qc.node_id,
        source_row_ref=f"qc.tsv:{row_suffix}",
        confidence=1.0,
        reason=f"run R{row_suffix} is caution for carryover",
    )
    return True


def _add_imputed_protein_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    protein, peptide, claim = _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=claim_ref,
        row_suffix=row_suffix,
    )
    quant_value = builder.add_quant_value(
        f"quant:{protein_id}",
        label=f"quant:{protein_id}",
        trust_class="imputed",
    )
    builder.add_protein_quantified_by_quant_value(
        protein.node_id,
        quant_value.node_id,
        source_row_ref=f"protein_matrix.tsv:{row_suffix}",
        confidence=0.95,
        reason=f"protein matrix contains abundance for {protein_id}",
    )
    builder.add_quant_value_supports_statistical_result(
        quant_value.node_id,
        claim.node_id,
        source_row_ref=f"quant_stats.tsv:{row_suffix}",
        confidence=0.92,
        reason=f"imputed quant value supports final statistic for {protein_id}",
    )
    return True


def _add_low_localization_ptm_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    ptm_ref: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    protein, peptide, _protein_claim = _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=None,
        row_suffix=f"{row_suffix}a",
    )
    modified = builder.add_modified_peptide(
        f"{peptide_id}[Phospho@S3]",
        label=f"{peptide_id}[Phospho@S3]",
        trust_class="high",
    )
    ptm_site = builder.add_ptm_site(ptm_ref, label=ptm_ref, trust_class="high")
    claim = builder.add_statistical_result(
        claim_ref,
        label=f"PTM result {ptm_ref}",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PTM_SITE,
                entity_ref=ptm_ref,
            ),
        ),
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
        confidence=0.74,
        reason=f"localized site {ptm_ref} remains weak",
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
    return True


def _add_poor_reproducibility_pathway_claim(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    pathway_id: str,
    claim_ref: str,
    row_suffix: str,
) -> bool:
    protein, _peptide, _claim = _add_protein_claim_support(
        builder,
        protein_id=protein_id,
        peptide_id=peptide_id,
        claim_ref=None,
        row_suffix=row_suffix,
        protein_trust_class="single_run_only",
    )
    pathway = builder.add_pathway(pathway_id, label=pathway_id, trust_class="high")
    claim = builder.add_statistical_result(
        claim_ref,
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
    return True


def _add_protein_claim_support(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_id: str,
    peptide_id: str,
    claim_ref: str | None,
    row_suffix: str,
    with_run: bool = False,
    protein_trust_class: str = "high",
) -> tuple[ProteomicsEvidenceNode, ProteomicsEvidenceNode, ProteomicsEvidenceNode | None]:
    protein = builder.add_protein(protein_id, label=protein_id, trust_class=protein_trust_class)
    peptide = builder.add_peptide(peptide_id, label=peptide_id, trust_class="high")
    claim = None
    if claim_ref is not None:
        claim = builder.add_statistical_result(
            claim_ref,
            label=f"protein result {protein_id}",
            claim_state="changed",
            context_refs=(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                    entity_ref=protein_id,
                ),
            ),
        )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref=f"protein_matrix.tsv:{row_suffix}",
        confidence=0.95,
        reason=f"{peptide_id} quantifies {protein_id}",
    )
    if claim is not None:
        builder.add_protein_supports_statistical_result(
            protein.node_id,
            claim.node_id,
            source_row_ref=f"protein_stats.tsv:{row_suffix}",
            confidence=0.91,
            reason=f"{protein_id} supports final protein result",
        )
    if not with_run:
        spectrum = builder.add_spectrum(f"scan={row_suffix}", label=f"scan={row_suffix}", trust_class="high")
        psm = builder.add_psm(f"psm:{row_suffix}", label=f"psm:{row_suffix}", trust_class="high")
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
    return protein, peptide, claim
