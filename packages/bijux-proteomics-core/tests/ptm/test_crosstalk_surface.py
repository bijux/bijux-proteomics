# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import (
    PtmCrosstalkEvidenceSource,
    PtmCrosstalkRelationship,
    PtmLocalizationConfidenceTier,
    PtmMappedSiteAnnotationEntry,
    PtmSiteAnnotationMappingReport,
    PtmSiteAnnotationMappingSummary,
    PtmSiteDifferentialEntry,
    PtmSiteDifferentialReport,
    PtmSiteEntry,
    build_ptm_crosstalk_report,
)
from bijux_proteomics.quantification import NormalizationMethod
from bijux_proteomics.quantification.contracts import DifferentialAbundanceTestType


def _site_entry(
    site_key: str,
    *,
    protein_ref: str,
    residue: str,
    position: int,
    modification_name: str,
    localized_peptides: tuple[str, ...],
) -> PtmSiteEntry:
    return PtmSiteEntry(
        site_key=site_key,
        protein_ref=protein_ref,
        residue=residue,
        position=position,
        modification_name=modification_name,
        localization_score=12.0,
        best_q_value=0.01,
        spectrum_count=2,
        peptide_count=1,
        localized_peptides=localized_peptides,
        sample_ids=("C1", "T1"),
        target_decoy_label=TargetDecoyLabel.TARGET,
        candidate_positions=(position,),
        ambiguous=False,
        shared_peptide=False,
        provenance=ImportedEvidenceProvenance(
            source_engine="synthetic-ptm",
            source_files=("synthetic.tsv",),
            source_row_numbers=(2,),
            original_identifiers={"site_key": site_key},
        ),
    )


def _differential_entry(
    site_key: str,
    *,
    protein_ref: str,
    residue: str,
    position: int,
    modification_name: str,
    localized_peptides: tuple[str, ...],
    log2_fold_change: float,
) -> PtmSiteDifferentialEntry:
    return PtmSiteDifferentialEntry(
        site_key=site_key,
        protein_ref=protein_ref,
        residue=residue,
        position=position,
        modification_name=modification_name,
        localization_tier=PtmLocalizationConfidenceTier.SUPPORTED,
        low_localization=False,
        ambiguous=False,
        shared_peptide=False,
        localized_peptides=localized_peptides,
        condition_a="control",
        condition_b="treated",
        observations_a=2,
        observations_b=2,
        complete_pair_count=0,
        mean_log2_abundance_a=10.0,
        mean_log2_abundance_b=10.0 + log2_fold_change,
        log2_fold_change=log2_fold_change,
        p_value=0.01,
        adjusted_p_value=0.02,
        standard_error=0.1,
        confidence_interval_low=log2_fold_change - 0.1,
        confidence_interval_high=log2_fold_change + 0.1,
        effect_size_cohens_d=1.0,
        protein_log2_fold_change=None,
        protein_adjusted_p_value=None,
        corrected_log2_fold_change=None,
        protein_correction_status="not_requested",
        uncertainty_note=None,
    )


def test_ptm_crosstalk_report_preserves_exact_site_pairs_and_evidence() -> None:
    site_entries = (
        _site_entry(
            "P11111:S5:Phospho",
            protein_ref="P11111",
            residue="S",
            position=5,
            modification_name="Phospho",
            localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
        ),
        _site_entry(
            "P11111:T9:Acetyl",
            protein_ref="P11111",
            residue="T",
            position=9,
            modification_name="Acetyl",
            localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
        ),
        _site_entry(
            "P11111:Y20:Phospho",
            protein_ref="P11111",
            residue="Y",
            position=20,
            modification_name="Phospho",
            localized_peptides=("MPEPTIDEY[Phospho]K",),
        ),
        _site_entry(
            "P22222:S4:Phospho",
            protein_ref="P22222",
            residue="S",
            position=4,
            modification_name="Phospho",
            localized_peptides=("AS[Phospho]TYK",),
        ),
    )
    differential_report = PtmSiteDifferentialReport(
        normalization_method=NormalizationMethod.MEDIAN,
        test_type=DifferentialAbundanceTestType.WELCH_T_TEST,
        condition_a="control",
        condition_b="treated",
        entries=(
            _differential_entry(
                "P11111:S5:Phospho",
                protein_ref="P11111",
                residue="S",
                position=5,
                modification_name="Phospho",
                localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
                log2_fold_change=1.1,
            ),
            _differential_entry(
                "P11111:T9:Acetyl",
                protein_ref="P11111",
                residue="T",
                position=9,
                modification_name="Acetyl",
                localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
                log2_fold_change=0.8,
            ),
            _differential_entry(
                "P11111:Y20:Phospho",
                protein_ref="P11111",
                residue="Y",
                position=20,
                modification_name="Phospho",
                localized_peptides=("MPEPTIDEY[Phospho]K",),
                log2_fold_change=-0.7,
            ),
            _differential_entry(
                "P22222:S4:Phospho",
                protein_ref="P22222",
                residue="S",
                position=4,
                modification_name="Phospho",
                localized_peptides=("AS[Phospho]TYK",),
                log2_fold_change=-0.6,
            ),
        ),
        broken_pairs=(),
        note="synthetic differential input for PTM crosstalk proof",
    )
    annotation_mapping_report = PtmSiteAnnotationMappingReport(
        target_species="Homo sapiens",
        matched_annotations=(
            PtmMappedSiteAnnotationEntry(
                site_key="P11111:S5:Phospho",
                annotation_species="Homo sapiens",
                observed_species="Homo sapiens",
                protein_ref="P11111",
                residue="S",
                position=5,
                modification_name="Phospho",
                site_function=None,
                kinases=(),
                phosphatases=(),
                pathways=("MAPK signaling",),
                source_name="Synthetic",
                source_accession="SYN1",
                ambiguous_site=False,
                shared_peptide_site=False,
            ),
            PtmMappedSiteAnnotationEntry(
                site_key="P11111:Y20:Phospho",
                annotation_species="Homo sapiens",
                observed_species="Homo sapiens",
                protein_ref="P11111",
                residue="Y",
                position=20,
                modification_name="Phospho",
                site_function=None,
                kinases=(),
                phosphatases=(),
                pathways=("MAPK signaling",),
                source_name="Synthetic",
                source_accession="SYN2",
                ambiguous_site=False,
                shared_peptide_site=False,
            ),
            PtmMappedSiteAnnotationEntry(
                site_key="P22222:S4:Phospho",
                annotation_species="Homo sapiens",
                observed_species="Homo sapiens",
                protein_ref="P22222",
                residue="S",
                position=4,
                modification_name="Phospho",
                site_function=None,
                kinases=(),
                phosphatases=(),
                pathways=("MAPK signaling",),
                source_name="Synthetic",
                source_accession="SYN3",
                ambiguous_site=False,
                shared_peptide_site=False,
            ),
        ),
        unmapped_annotations=(),
        summary=PtmSiteAnnotationMappingSummary(
            matched_annotation_count=3,
            matched_site_count=3,
            unmapped_annotation_count=0,
            species_mismatch_count=0,
        ),
        note="synthetic pathway context for PTM crosstalk proof",
    )

    report = build_ptm_crosstalk_report(
        site_entries,
        differential_report,
        annotation_mapping_report=annotation_mapping_report,
        nearby_residue_distance=6,
    )

    assert report.summary.pair_count == 5
    assert report.summary.co_changing_pair_count == 2
    assert report.summary.opposing_pair_count == 3
    assert report.summary.same_peptide_pair_count == 1
    assert report.summary.nearby_residue_pair_count == 1
    assert report.summary.shared_pathway_pair_count == 3

    same_peptide_pair = next(
        entry
        for entry in report.entries
        if entry.left_site_key == "P11111:S5:Phospho"
        and entry.right_site_key == "P11111:T9:Acetyl"
    )
    assert same_peptide_pair.relationship is PtmCrosstalkRelationship.CO_CHANGING
    assert same_peptide_pair.shared_peptides == ("S[Phospho]PEP[Acetyl]TIDEK",)
    assert same_peptide_pair.residue_distance == 4
    assert {
        PtmCrosstalkEvidenceSource.SAME_PROTEIN,
        PtmCrosstalkEvidenceSource.SAME_PEPTIDE,
        PtmCrosstalkEvidenceSource.NEARBY_RESIDUES,
    } == set(same_peptide_pair.evidence_sources)

    opposing_pathway_pair = next(
        entry
        for entry in report.entries
        if entry.left_site_key == "P11111:S5:Phospho"
        and entry.right_site_key == "P11111:Y20:Phospho"
    )
    assert opposing_pathway_pair.relationship is PtmCrosstalkRelationship.OPPOSING
    assert opposing_pathway_pair.shared_pathways == ("MAPK signaling",)
    assert (
        PtmCrosstalkEvidenceSource.SHARED_PATHWAY
        in opposing_pathway_pair.evidence_sources
    )

    pathway_only_pair = next(
        entry
        for entry in report.entries
        if entry.left_site_key == "P11111:Y20:Phospho"
        and entry.right_site_key == "P22222:S4:Phospho"
    )
    assert pathway_only_pair.relationship is PtmCrosstalkRelationship.CO_CHANGING
    assert pathway_only_pair.evidence_sources == (
        PtmCrosstalkEvidenceSource.SHARED_PATHWAY,
    )

    protein_map = next(
        entry for entry in report.protein_maps if entry.protein_ref == "P11111"
    )
    assert protein_map.site_keys == (
        "P11111:S5:Phospho",
        "P11111:T9:Acetyl",
        "P11111:Y20:Phospho",
    )
    assert protein_map.co_changing_pair_count == 1
    assert protein_map.opposing_pair_count == 2
