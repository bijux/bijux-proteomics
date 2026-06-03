# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    build_review_ready_evidence_bundle,
    filter_psms_by_fdr,
    parse_psm_tsv,
)
from bijux_proteomics.identification.contracts import ReviewReadyEvidenceBundle
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import (
    build_ptm_lab_validation_packet,
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantRollupMethod,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.review import (
    QuantReviewBundle,
    build_quant_review_bundle,
)
from bijux_proteomics.review import (
    ScientificConsistencyIssueCode,
    build_workflow_scientific_snapshot,
    evaluate_workflow_scientific_consistency,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.digestion import digest_protein_records
from bijux_proteomics_lab.handoffs.ptm import PtmLabValidationPacket


def _fixture(*parts: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / Path(*parts)


def _mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def _bundle() -> ReviewReadyEvidenceBundle:
    report = parse_psm_tsv(
        _fixture("psm", "protein_inference_results.tsv"),
        mapping=_mapping(),
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)
    return cast(
        ReviewReadyEvidenceBundle,
        build_review_ready_evidence_bundle(
            accepted,
            threshold=0.05,
            score_orientation="higher_better",
            ptm_site_keys_by_peptide={"SHAREDK": ("P11111:S5:Phospho",)},
            quant_support_by_protein={"P11111": {"C1": 2200.0}},
        ),
    )


def _quant_bundle(*, heavily_missing: bool) -> QuantReviewBundle:
    records = (
        Ms1FeatureRecord(
            feature_id="q-1",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-2",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=980.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-3",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=0.0,
            protein_refs=("P11111",),
            missing_value_kind=(
                MissingValueKind.NOT_OBSERVED
                if heavily_missing
                else MissingValueKind.OBSERVED
            ),
        ),
        Ms1FeatureRecord(
            feature_id="q-4",
            sample_id="s4",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=0.0,
            protein_refs=("P11111",),
            missing_value_kind=(
                MissingValueKind.NOT_OBSERVED
                if heavily_missing
                else MissingValueKind.OBSERVED
            ),
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="b2",
        ),
    )
    return build_quant_review_bundle(
        records,
        design_entries=design,
        normalization_method=NormalizationMethod.MEDIAN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def _ptm_packet() -> PtmLabValidationPacket:
    parsed = parse_ptm_localization_tsv(_fixture("ptm", "localization_results.tsv"))
    fasta = parse_fasta_document(
        _fixture("fasta", "ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    sequences = {
        record.canonical_accession: record.residues for record in fasta.accepted_records
    }
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=sequences,
    )
    sites = tuple(
        site
        for site in build_ptm_site_table(mappings)
        if not site.site_key.startswith("Q9DEC1:")
    )
    features = parse_ms1_feature_table(
        _fixture("ptm", "ptm_features.tsv")
    ).accepted_records
    trimmed_features = tuple(
        record
        for record in features
        if not (record.sample_id == "T2" and record.canonical_peptide == "SPEPTIDEK")
    )
    occupancy = build_ptm_occupancy_counterpart_report(
        sites, feature_records=trimmed_features
    )
    return build_ptm_lab_validation_packet(sites, occupancy_report=occupancy)


def _digested_peptides() -> int:
    report = parse_fasta_document(
        _fixture("fasta", "ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    return len(digest_protein_records(report.accepted_records))


def test_scientific_story_regression_blocks_empty_digestion_space() -> None:
    snapshot = build_workflow_scientific_snapshot(
        workflow_id="wf-empty-digest",
        identification_bundle=_bundle(),
        quant_review_bundle=_quant_bundle(heavily_missing=False),
        ptm_lab_validation_packet=_ptm_packet(),
        quant_support_protein_ids=("P11111",),
        digested_peptide_count=0,
        review_candidate_ids=("candidate-1",),
    )

    report = evaluate_workflow_scientific_consistency(snapshot)

    assert any(
        issue.code is ScientificConsistencyIssueCode.EMPTY_DIGESTION_SPACE
        for issue in report.issues
    )


def test_scientific_story_regression_blocks_decision_grade_under_high_missingness() -> (
    None
):
    snapshot = build_workflow_scientific_snapshot(
        workflow_id="wf-missingness",
        identification_bundle=_bundle(),
        quant_review_bundle=_quant_bundle(heavily_missing=True),
        ptm_lab_validation_packet=_ptm_packet(),
        quant_support_protein_ids=("P11111",),
        digested_peptide_count=_digested_peptides(),
        review_candidate_ids=("candidate-1",),
        decision_grade_requested=True,
    )

    report = evaluate_workflow_scientific_consistency(snapshot)

    assert any(
        issue.code
        is ScientificConsistencyIssueCode.DECISION_GRADE_WITH_HIGH_MISSINGNESS
        for issue in report.issues
    )


def test_scientific_story_regression_blocks_decision_grade_under_ambiguous_ptm() -> (
    None
):
    snapshot = build_workflow_scientific_snapshot(
        workflow_id="wf-ptm",
        identification_bundle=_bundle(),
        quant_review_bundle=_quant_bundle(heavily_missing=False),
        ptm_lab_validation_packet=_ptm_packet(),
        quant_support_protein_ids=("P11111",),
        digested_peptide_count=_digested_peptides(),
        review_candidate_ids=("candidate-1",),
        decision_grade_requested=True,
    )

    report = evaluate_workflow_scientific_consistency(snapshot)

    assert any(
        issue.code is ScientificConsistencyIssueCode.DECISION_GRADE_WITH_AMBIGUOUS_PTM
        for issue in report.issues
    )


def test_scientific_story_regression_blocks_decision_grade_without_review_projection() -> (
    None
):
    snapshot = build_workflow_scientific_snapshot(
        workflow_id="wf-review-gap",
        identification_bundle=_bundle(),
        quant_review_bundle=_quant_bundle(heavily_missing=False),
        ptm_lab_validation_packet=_ptm_packet(),
        quant_support_protein_ids=("P11111",),
        digested_peptide_count=_digested_peptides(),
        review_candidate_ids=(),
        decision_grade_requested=True,
    )

    report = evaluate_workflow_scientific_consistency(snapshot)

    assert any(
        issue.code
        is ScientificConsistencyIssueCode.REVIEW_PROJECTION_WITHOUT_CANDIDATES
        for issue in report.issues
    )
