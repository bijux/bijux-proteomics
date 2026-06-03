# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatographic_evidence import (
    ChromatographicEvidenceScoreReport,
    ChromatographicPeptideEvidenceEntry,
)
from bijux_proteomics.io.dia_fragment_coelution import (
    extract_mzml_dia_fragment_trace_coelution,
)
from bijux_proteomics.io.fragment_ratio_stability import (
    FragmentRatioDataKind,
    FragmentRatioStabilityFragmentEntry,
    FragmentRatioStabilityObservationEntry,
    FragmentRatioStabilityReport,
    FragmentRatioStabilitySummary,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
)
from bijux_proteomics.quantification.matrix.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics.quantification.peptide_profile_inconsistency import (
    PeptideProfileInconsistencyEntry,
    PeptideProfileInconsistencyReport,
    PeptideProfileInconsistencySummary,
    PeptideProfileOutlierReason,
)
from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
    propagate_evidence_graph_confidence,
)
from bijux_proteomics.sequences import build_peptide_chemical_liability_report


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def build_confidence_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    strong_spectrum = builder.add_spectrum(
        "scan=1001", label="scan=1001", trust_class="high"
    )
    weak_spectrum = builder.add_spectrum(
        "scan=1002", label="scan=1002", trust_class="low"
    )
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


def build_precursor_confidence_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    strong_spectrum = builder.add_spectrum(
        "scan=2001", label="scan=2001", trust_class="high"
    )
    shifted_spectrum = builder.add_spectrum(
        "scan=2002", label="scan=2002", trust_class="high"
    )
    strong_precursor = builder.add_precursor(
        "prec_alpha",
        label="prec_alpha",
        trust_class="high",
    )
    shifted_precursor = builder.add_precursor(
        "prec_beta",
        label="prec_beta",
        trust_class="high",
    )
    strong_peptide = builder.add_peptide("PEPA", label="PEPA", trust_class="high")
    shifted_peptide = builder.add_peptide("PEPB", label="PEPB", trust_class="high")
    strong_protein = builder.add_protein("P33333", label="P33333", trust_class="high")
    shifted_protein = builder.add_protein("P44444", label="P44444", trust_class="high")

    strong_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P33333",
        label="strong precursor-backed result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P33333",
            ),
        ),
    )
    shifted_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P44444",
        label="shifted precursor-backed result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P44444",
            ),
        ),
    )

    builder.add_spectrum_assigns_precursor(
        strong_spectrum.node_id,
        strong_precursor.node_id,
        source_row_ref="dia_precursors.tsv:4",
        confidence=0.95,
        reason="accepted DIA precursor assignment",
    )
    builder.add_spectrum_assigns_precursor(
        shifted_spectrum.node_id,
        shifted_precursor.node_id,
        source_row_ref="dia_precursors.tsv:5",
        confidence=0.95,
        reason="accepted DIA precursor assignment",
    )
    builder.add_precursor_supports_peptide(
        strong_precursor.node_id,
        strong_peptide.node_id,
        source_row_ref="dia_peptides.tsv:4",
        confidence=0.93,
        reason="coeluting DIA fragments support PEPA",
    )
    builder.add_precursor_supports_peptide(
        shifted_precursor.node_id,
        shifted_peptide.node_id,
        source_row_ref="dia_peptides.tsv:5",
        confidence=0.93,
        reason="shifted DIA fragments support PEPB",
    )
    builder.add_peptide_quantifies_protein(
        strong_peptide.node_id,
        strong_protein.node_id,
        source_row_ref="protein_matrix.tsv:10",
        confidence=0.92,
        reason="PEPA quantifies P33333",
    )
    builder.add_peptide_quantifies_protein(
        shifted_peptide.node_id,
        shifted_protein.node_id,
        source_row_ref="protein_matrix.tsv:11",
        confidence=0.92,
        reason="PEPB quantifies P44444",
    )
    builder.add_protein_supports_statistical_result(
        strong_protein.node_id,
        strong_result.node_id,
        source_row_ref="protein_stats.tsv:10",
        confidence=0.91,
        reason="P33333 differential result",
    )
    builder.add_protein_supports_statistical_result(
        shifted_protein.node_id,
        shifted_result.node_id,
        source_row_ref="protein_stats.tsv:11",
        confidence=0.91,
        reason="P44444 differential result",
    )
    return builder.build()


def test_propagate_evidence_graph_confidence_depends_on_upstream_quality() -> None:
    report = propagate_evidence_graph_confidence(build_confidence_fixture_graph())

    assert report.entry_count == 5
    assert len(report.tier_counts) > 1

    by_claim = {entry.claim_node_ref: entry for entry in report.entries}
    assert (
        by_claim["protein:treatment_vs_control:P11111"].confidence_tier.value == "high"
    )
    assert (
        by_claim["protein:treatment_vs_control:P22222"].confidence_tier.value == "low"
    )
    assert (
        by_claim["protein:treatment_vs_control:P11111"].propagated_score
        > by_claim["protein:treatment_vs_control:P22222"].propagated_score
    )
    assert (
        by_claim["ptm:treatment_vs_control:P11111:S3:Phospho"].confidence_tier.value
        == "high"
    )
    assert (
        by_claim["pathway:treatment_vs_control:R-HSA-199420"].confidence_tier.value
        == "high"
    )
    assert (
        by_claim["pathway:treatment_vs_control:R-HSA-6802957"].confidence_tier.value
        == "low"
    )


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


def test_propagate_evidence_graph_confidence_penalizes_shifted_dia_fragments() -> None:
    coelution_report = extract_mzml_dia_fragment_trace_coelution(
        (_format_fixture("dia_fragment_coelution.mzml"),),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
    )

    report = propagate_evidence_graph_confidence(
        build_precursor_confidence_fixture_graph(),
        dia_fragment_coelution_report=coelution_report,
    )

    by_claim = {entry.claim_node_ref: entry for entry in report.entries}
    strong_entry = by_claim["protein:treatment_vs_control:P33333"]
    shifted_entry = by_claim["protein:treatment_vs_control:P44444"]

    assert strong_entry.confidence_tier.value == "high"
    assert strong_entry.propagated_score > shifted_entry.propagated_score
    assert shifted_entry.confidence_tier.value in {"moderate", "low"}


def test_propagate_evidence_graph_confidence_penalizes_unstable_fragment_ratios() -> (
    None
):
    ratio_report = FragmentRatioStabilityReport(
        data_kind=FragmentRatioDataKind.DIA,
        fragment_entries=(
            FragmentRatioStabilityFragmentEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_alpha",
                peptide_ref="PEPA",
                fragment_id="alpha_y7",
                run_count=2,
                observed_run_count=2,
                expected_ratio=0.6,
                ratio_cv=0.03,
                drift_flagged_run_count=0,
                unstable_fragment=False,
                stability_score=0.96,
            ),
            FragmentRatioStabilityFragmentEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_alpha",
                peptide_ref="PEPA",
                fragment_id="alpha_y8",
                run_count=2,
                observed_run_count=2,
                expected_ratio=0.4,
                ratio_cv=0.04,
                drift_flagged_run_count=0,
                unstable_fragment=False,
                stability_score=0.94,
            ),
            FragmentRatioStabilityFragmentEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_beta",
                peptide_ref="PEPB",
                fragment_id="beta_y7",
                run_count=2,
                observed_run_count=2,
                expected_ratio=0.6,
                ratio_cv=0.42,
                drift_flagged_run_count=2,
                unstable_fragment=True,
                stability_score=0.28,
                concern_codes=("ratio_drift", "high_ratio_cv"),
            ),
            FragmentRatioStabilityFragmentEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_beta",
                peptide_ref="PEPB",
                fragment_id="beta_y8",
                run_count=2,
                observed_run_count=2,
                expected_ratio=0.4,
                ratio_cv=0.39,
                drift_flagged_run_count=2,
                unstable_fragment=True,
                stability_score=0.24,
                concern_codes=("ratio_drift", "high_ratio_cv"),
            ),
        ),
        observation_entries=(
            FragmentRatioStabilityObservationEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_alpha",
                peptide_ref="PEPA",
                run_id="run_alpha",
                fragment_id="alpha_y7",
                expected_ratio=0.6,
                observed_ratio=0.59,
                absolute_ratio_delta=0.01,
                ratio_cv=0.03,
            ),
            FragmentRatioStabilityObservationEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_alpha",
                peptide_ref="PEPA",
                run_id="run_beta",
                fragment_id="alpha_y8",
                expected_ratio=0.4,
                observed_ratio=0.41,
                absolute_ratio_delta=0.01,
                ratio_cv=0.04,
            ),
            FragmentRatioStabilityObservationEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_beta",
                peptide_ref="PEPB",
                run_id="run_alpha",
                fragment_id="beta_y7",
                expected_ratio=0.6,
                observed_ratio=0.33,
                absolute_ratio_delta=0.27,
                ratio_cv=0.42,
                drift_flag=True,
                unstable_fragment=True,
                concern_codes=("ratio_drift", "high_ratio_cv"),
            ),
            FragmentRatioStabilityObservationEntry(
                data_kind=FragmentRatioDataKind.DIA,
                analyte_id="prec_beta",
                peptide_ref="PEPB",
                run_id="run_beta",
                fragment_id="beta_y8",
                expected_ratio=0.4,
                observed_ratio=0.67,
                absolute_ratio_delta=0.27,
                ratio_cv=0.39,
                drift_flag=True,
                unstable_fragment=True,
                concern_codes=("ratio_drift", "high_ratio_cv"),
            ),
        ),
        summary=FragmentRatioStabilitySummary(
            analyte_count=2,
            run_count=2,
            fragment_entry_count=4,
            observation_entry_count=4,
            unstable_fragment_count=2,
            drift_flagged_observation_count=2,
        ),
        note="synthetic dia fragment ratio stability report",
    )

    baseline = propagate_evidence_graph_confidence(
        build_precursor_confidence_fixture_graph()
    )
    with_ratio_stability = propagate_evidence_graph_confidence(
        build_precursor_confidence_fixture_graph(),
        dia_fragment_ratio_stability_report=ratio_report,
    )

    baseline_by_claim = {entry.claim_node_ref: entry for entry in baseline.entries}
    with_ratio_by_claim = {
        entry.claim_node_ref: entry for entry in with_ratio_stability.entries
    }

    assert (
        baseline_by_claim["protein:treatment_vs_control:P33333"].propagated_score
        == baseline_by_claim["protein:treatment_vs_control:P44444"].propagated_score
    )
    assert (
        with_ratio_by_claim["protein:treatment_vs_control:P33333"].propagated_score
        > with_ratio_by_claim["protein:treatment_vs_control:P44444"].propagated_score
    )
    assert (
        "fragment-ratio stability"
        in with_ratio_by_claim["protein:treatment_vs_control:P33333"].rationale
    )


def test_propagate_evidence_graph_confidence_absorbs_chromatographic_peptide_scores() -> (
    None
):
    builder = ProteomicsEvidenceGraphBuilder()

    spectrum_a = builder.add_spectrum(
        "scan=2001", label="scan=2001", trust_class="high"
    )
    spectrum_b = builder.add_spectrum(
        "scan=2002", label="scan=2002", trust_class="high"
    )
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
        > chromatographic_by_claim[
            "protein:treatment_vs_control:P30002"
        ].propagated_score
    )
    assert (
        chromatographic_by_claim[
            "protein:treatment_vs_control:P30001"
        ].confidence_tier.value
        == "high"
    )
    assert (
        chromatographic_by_claim[
            "protein:treatment_vs_control:P30002"
        ].confidence_tier.value
        == "moderate"
    )
    assert (
        "peptide chromatographic evidence"
        in chromatographic_by_claim["protein:treatment_vs_control:P30001"].rationale
    )


def test_propagate_evidence_graph_confidence_uses_peptide_chemical_liability() -> None:
    builder = ProteomicsEvidenceGraphBuilder()

    safe_spectrum = builder.add_spectrum(
        "scan=3001", label="scan=3001", trust_class="high"
    )
    risky_spectrum = builder.add_spectrum(
        "scan=3002", label="scan=3002", trust_class="high"
    )
    safe_psm = builder.add_psm("psm:3001", label="psm:3001", trust_class="high")
    risky_psm = builder.add_psm("psm:3002", label="psm:3002", trust_class="high")
    safe_peptide = builder.add_peptide("ATIDEAR", label="ATIDEAR", trust_class="high")
    risky_peptide = builder.add_peptide(
        "MNNQVVVVVVILKKDG",
        label="MNNQVVVVVVILKKDG",
        trust_class="high",
    )
    safe_protein = builder.add_protein("P55555", label="P55555", trust_class="high")
    risky_protein = builder.add_protein("P66666", label="P66666", trust_class="high")
    safe_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P55555",
        label="safe peptide-backed result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P55555",
            ),
        ),
    )
    risky_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P66666",
        label="risky peptide-backed result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P66666",
            ),
        ),
    )

    for row_number, spectrum, psm, peptide, protein, result in (
        (1, safe_spectrum, safe_psm, safe_peptide, safe_protein, safe_result),
        (2, risky_spectrum, risky_psm, risky_peptide, risky_protein, risky_result),
    ):
        builder.add_spectrum_supports_psm(
            spectrum.node_id,
            psm.node_id,
            source_row_ref=f"psm.tsv:{row_number}",
            confidence=0.95,
            reason="accepted spectrum supports PSM",
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
    report = propagate_evidence_graph_confidence(
        graph,
        peptide_liability_reports=(
            build_peptide_chemical_liability_report("ATIDEAR"),
            build_peptide_chemical_liability_report("MNNQVVVVVVILKKDG", charge=4),
        ),
    )

    by_subject = {entry.subject_node_ref: entry for entry in report.entries}
    strong_entry = by_subject["P55555"]
    risky_entry = by_subject["P66666"]

    assert strong_entry.propagated_score > risky_entry.propagated_score
    assert "peptide chemical liability" in risky_entry.rationale


def test_propagate_evidence_graph_confidence_penalizes_inconsistent_peptide_profiles() -> (
    None
):
    builder = ProteomicsEvidenceGraphBuilder()

    strong_spectrum = builder.add_spectrum(
        "scan=4001", label="scan=4001", trust_class="high"
    )
    inconsistent_spectrum = builder.add_spectrum(
        "scan=4002",
        label="scan=4002",
        trust_class="high",
    )
    strong_psm = builder.add_psm("psm:4001", label="psm:4001", trust_class="high")
    inconsistent_psm = builder.add_psm(
        "psm:4002",
        label="psm:4002",
        trust_class="high",
    )
    strong_peptide = builder.add_peptide("PEPA", label="PEPA", trust_class="high")
    inconsistent_peptide = builder.add_peptide(
        "PEPVVK",
        label="PEPVVK",
        trust_class="high",
    )
    strong_protein = builder.add_protein("P77771", label="P77771", trust_class="high")
    inconsistent_protein = builder.add_protein(
        "P77772",
        label="P77772",
        trust_class="high",
    )
    strong_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P77771",
        label="consistent peptide-backed result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P77771",
            ),
        ),
    )
    inconsistent_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P77772",
        label="inconsistent peptide-backed result",
        claim_state="changed",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P77772",
            ),
        ),
    )

    for row_number, spectrum, psm, peptide, protein, result in (
        (
            41,
            strong_spectrum,
            strong_psm,
            strong_peptide,
            strong_protein,
            strong_result,
        ),
        (
            42,
            inconsistent_spectrum,
            inconsistent_psm,
            inconsistent_peptide,
            inconsistent_protein,
            inconsistent_result,
        ),
    ):
        builder.add_spectrum_supports_psm(
            spectrum.node_id,
            psm.node_id,
            source_row_ref=f"psm.tsv:{row_number}",
            confidence=0.95,
            reason="accepted spectrum supports PSM",
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
    with_inconsistency = propagate_evidence_graph_confidence(
        graph,
        peptide_profile_inconsistency_report=PeptideProfileInconsistencyReport(
            source_kind=PeptideMatrixSourceKind.FEATURE,
            grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
            target_kind=ProteinMatrixTargetKind.PROTEIN,
            unique_only=False,
            sample_ids=("S1", "S2", "S3"),
            entries=(
                PeptideProfileInconsistencyEntry(
                    entity_id="P77771",
                    target_kind=ProteinMatrixTargetKind.PROTEIN,
                    peptide_id="PEPA",
                    peptide_sequence="PEPA",
                    protein_refs=("P77771",),
                    reference_peptide_ids=("PEPC", "PEPD"),
                    overlap_sample_count=3,
                    reference_peptide_count=2,
                    correlation_to_protein_profile=1.0,
                    residual_rmsd_log2=0.05,
                    max_abs_residual_log2=0.08,
                    profile_agreement_score=1.0,
                    inconsistent_with_protein_profile=False,
                    outlier_reason=PeptideProfileOutlierReason.CONSISTENT,
                    sample_residuals=(),
                ),
                PeptideProfileInconsistencyEntry(
                    entity_id="P77772",
                    target_kind=ProteinMatrixTargetKind.PROTEIN,
                    peptide_id="PEPVVK",
                    peptide_sequence="PEPVVK",
                    protein_refs=("P77772",),
                    reference_peptide_ids=("PEPA", "PEPC", "PEPD"),
                    overlap_sample_count=3,
                    reference_peptide_count=3,
                    correlation_to_protein_profile=-1.0,
                    residual_rmsd_log2=1.97,
                    max_abs_residual_log2=2.04,
                    profile_agreement_score=0.2,
                    inconsistent_with_protein_profile=True,
                    outlier_reason=(
                        PeptideProfileOutlierReason.DIRECTIONAL_PROFILE_INVERSION
                    ),
                    sample_residuals=(),
                ),
            ),
            summary=PeptideProfileInconsistencySummary(
                peptide_row_count=4,
                protein_row_count=2,
                evaluated_entry_count=2,
                inconsistent_entry_count=1,
                insufficient_overlap_entry_count=0,
            ),
            note="synthetic peptide profile inconsistency report",
        ),
    )

    baseline_by_claim = {entry.claim_node_ref: entry for entry in baseline.entries}
    inconsistency_by_claim = {
        entry.claim_node_ref: entry for entry in with_inconsistency.entries
    }

    assert (
        baseline_by_claim["protein:treatment_vs_control:P77771"].propagated_score
        == baseline_by_claim["protein:treatment_vs_control:P77772"].propagated_score
    )
    assert (
        inconsistency_by_claim["protein:treatment_vs_control:P77771"].propagated_score
        > inconsistency_by_claim["protein:treatment_vs_control:P77772"].propagated_score
    )
    assert (
        "peptide profile inconsistency"
        in inconsistency_by_claim["protein:treatment_vs_control:P77772"].rationale
    )
