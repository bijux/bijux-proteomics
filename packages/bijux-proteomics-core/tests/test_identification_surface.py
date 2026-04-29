# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    apply_q_values,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    build_peptide_summary_report,
    build_protein_summary_report,
    build_psm_summary_report,
    build_search_result_provenance_manifest,
    compute_fdr_reproducibility_hash,
    export_psm_tsv,
    FdrPolicy,
    filter_psms_by_fdr,
    normalize_psm_score_orientation,
    PsmSortField,
    PsmRecord,
    SearchResultColumnMapping,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    export_psm_jsonl,
    normalize_psm_records,
    parse_psm_tsv,
    parse_target_decoy_label,
    rollup_peptide_evidence,
    rollup_protein_evidence,
    select_best_psm_per_spectrum,
    sort_psm_records,
)


def _psm_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "psm" / name


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_psm_model_and_tsv_parser_accept_minimal_fixture() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())

    assert report.total_rows == 3
    assert len(report.accepted_records) == 3
    first = report.accepted_records[0]
    assert first.spectrum_id == "scan=1001"
    assert first.canonical_peptide == "PEPTIDE"
    assert first.charge == 2
    assert first.q_value == 0.01


def test_search_result_column_mapping_supports_engine_specific_headers() -> None:
    mapping = SearchResultColumnMapping(
        spectrum_id="SpecID",
        peptide="Sequence",
        charge="Z",
        score="PrimaryScore",
        q_value="PosteriorError",
        protein_refs="Proteins",
        decoy_label="DecoyFlag",
    )

    report = parse_psm_tsv(_psm_fixture("engine_mapped_results.tsv"), mapping=mapping)

    assert len(report.accepted_records) == 3
    assert report.accepted_records[1].canonical_peptide == "PES[Phospho]TIDE"
    assert report.accepted_records[2].target_decoy_label is TargetDecoyLabel.DECOY


def test_search_result_validation_rejects_missing_and_bad_fields() -> None:
    report = parse_psm_tsv(_psm_fixture("malformed_results.tsv"), mapping=_default_mapping())

    assert len(report.accepted_records) == 0
    assert len(report.rejected_rows) == 4
    codes = {
        issue.code
        for rejected in report.rejected_rows
        for issue in rejected.issues
    }
    assert {"missing_spectrum_id", "missing_peptide", "invalid_charge", "invalid_score"} <= codes


def test_normalization_exports_stable_jsonl() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    normalized = normalize_psm_records(report.accepted_records)
    output_path = _psm_fixture("normalized.jsonl")
    try:
        export_psm_jsonl(normalized, output_path)
        lines = output_path.read_text().strip().splitlines()
        assert len(lines) == 3
        payload = json.loads(lines[0])
        assert payload["spectrum_id"] == "scan=1001"
    finally:
        output_path.unlink(missing_ok=True)


def test_target_decoy_label_parser_supports_prefix_suffix_and_explicit_labels() -> None:
    prefix_label = parse_target_decoy_label(protein_refs=("DECOY_P99999",))
    suffix_label = parse_target_decoy_label(
        protein_refs=("P12345_decoy",),
        policy=TargetDecoyLabelPolicy(protein_prefix=None, protein_suffix="_decoy"),
    )
    explicit_label = parse_target_decoy_label(explicit_label="decoy")

    assert prefix_label is TargetDecoyLabel.DECOY
    assert suffix_label is TargetDecoyLabel.DECOY
    assert explicit_label is TargetDecoyLabel.DECOY


def test_psm_sorting_policy_covers_spectrum_score_qvalue_and_peptide() -> None:
    report = parse_psm_tsv(_psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping())

    by_spectrum = sort_psm_records(report.accepted_records, by=PsmSortField.SPECTRUM)
    by_score = sort_psm_records(report.accepted_records, by=PsmSortField.SCORE)
    by_q_value = sort_psm_records(report.accepted_records, by=PsmSortField.Q_VALUE)
    by_peptide = sort_psm_records(report.accepted_records, by=PsmSortField.PEPTIDE)

    assert by_spectrum[0].spectrum_id == "scan=2001"
    assert by_score[0].score == 51.0
    assert by_q_value[0].q_value == 0.01
    assert by_peptide[0].canonical_peptide == "PEPTIDE"


def test_best_psm_per_spectrum_selector_prefers_highest_score() -> None:
    report = parse_psm_tsv(_psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping())
    selected = select_best_psm_per_spectrum(report.accepted_records)

    assert len(selected) == 2
    best_scan_2001 = next(record for record in selected if record.spectrum_id == "scan=2001")
    assert best_scan_2001.canonical_peptide == "PEPTIDER"
    assert best_scan_2001.score == 47.0


def test_peptide_level_rollup_combines_multiple_psms() -> None:
    report = parse_psm_tsv(_psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping())
    rollups = rollup_peptide_evidence(report.accepted_records)

    assert len(rollups) == 2
    peptide_rollup = next(rollup for rollup in rollups if rollup.canonical_peptide == "PEPTIDER")
    assert peptide_rollup.psm_count == 2
    assert peptide_rollup.spectrum_count == 2
    assert peptide_rollup.protein_refs == ("P12345", "Q11111")


def test_protein_level_evidence_rollup_counts_unique_and_shared_peptides() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    rollups = rollup_protein_evidence(report.accepted_records)

    protein_rollup = next(rollup for rollup in rollups if rollup.protein_ref == "P12345")
    shared_rollup = next(rollup for rollup in rollups if rollup.protein_ref == "Q22222")
    decoy_rollup = next(rollup for rollup in rollups if rollup.protein_ref == "DECOY_P99999")

    assert protein_rollup.unique_peptide_count == 1
    assert protein_rollup.shared_peptide_count == 1
    assert shared_rollup.unique_peptide_count == 0
    assert decoy_rollup.target_decoy_label is TargetDecoyLabel.DECOY


def test_basic_target_decoy_fdr_and_q_values_are_monotonic() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    annotated = apply_q_values(report.accepted_records)

    assert [record.q_value for record in annotated] == sorted(
        (record.q_value for record in annotated)
    )
    assert annotated[0].q_value == 0.0
    assert annotated[-1].q_value == 2 / 3


def test_fdr_threshold_filter_keeps_requested_cutoff() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.5)

    assert len(accepted) == 3
    strict = filter_psms_by_fdr(report.accepted_records, threshold=0.34)
    assert len(strict) == 1


def test_score_orientation_normalization_supports_higher_and_lower_better() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    higher = normalize_psm_score_orientation(report.accepted_records, score_orientation="higher_better")
    lower = normalize_psm_score_orientation(report.accepted_records, score_orientation="lower_better")

    assert higher[0].raw_score == 100.0
    assert higher[0].normalized_score == 1.0
    assert lower[0].raw_score == 80.0
    assert lower[0].normalized_score == 1.0


def test_fdr_audit_trail_and_calibration_bins_are_stable() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    audit = build_fdr_audit_trail(
        report.accepted_records,
        threshold=0.5,
        score_orientation="higher_better",
    )
    calibration = build_calibration_plot_data(
        report.accepted_records,
        score_orientation="higher_better",
        bin_count=4,
    )

    assert len(audit.entries) == 5
    assert len(audit.reproducibility_hash) == 64
    assert audit.entries[-1].q_value >= audit.entries[0].q_value
    assert len(calibration.bins) == 4
    assert sum(bin.target_count + bin.decoy_count + bin.mixed_count + bin.unknown_count for bin in calibration.bins) == 5


def test_fdr_reproducibility_and_edge_cases_are_explicit() -> None:
    no_decoys = (
        PsmRecord(
            spectrum_id="scan-a",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=20.0,
            protein_refs=("P1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-b",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=20.0,
            protein_refs=("P2",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )
    all_decoys = tuple(
        record.model_copy(update={"target_decoy_label": TargetDecoyLabel.DECOY})
        for record in no_decoys
    )

    target_hash = compute_fdr_reproducibility_hash(no_decoys, threshold=0.01)
    repeated_hash = compute_fdr_reproducibility_hash(no_decoys, threshold=0.01)
    decoy_hash = compute_fdr_reproducibility_hash(all_decoys, threshold=0.01)
    annotated_decoys = apply_q_values(all_decoys)

    assert target_hash == repeated_hash
    assert target_hash != decoy_hash
    assert all(record.q_value == 1.0 for record in annotated_decoys)


def test_psm_summary_report_counts_labels_charges_and_score_bins() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    summary = build_psm_summary_report(report.accepted_records)

    assert summary.total_psms == 3
    assert summary.target_psms == 2
    assert summary.decoy_psms == 1
    assert summary.counts_by_charge["2"] == 2


def test_peptide_summary_report_counts_modified_and_shared_peptides() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    summary = build_peptide_summary_report(report.accepted_records)

    assert summary.total_peptides == 3
    assert summary.modified_peptides == 1
    assert summary.shared_peptides == 1


def test_protein_summary_report_supports_optional_coverage() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    summary = build_protein_summary_report(
        report.accepted_records,
        protein_lengths={"P12345": 20, "Q22222": 20, "DECOY_P99999": 20},
    )

    first = next(group for group in summary.protein_groups if group.protein_ref == "P12345")
    assert summary.total_proteins == 3
    assert first.coverage_fraction is not None
    assert 0.0 < first.coverage_fraction <= 1.0


def test_search_result_provenance_manifest_records_input_mapping_and_policy() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    manifest = build_search_result_provenance_manifest(
        source_path=_psm_fixture("minimal_results.tsv"),
        parse_report=report,
        decoy_policy=TargetDecoyLabelPolicy(),
        fdr_policy=FdrPolicy(threshold=0.01),
    )

    assert manifest.document_schema.document_kind == "search_result_provenance_manifest"
    assert manifest.source_sha256
    assert manifest.column_mapping.spectrum_id == "spectrum_id"
    assert manifest.fdr_policy is not None


def test_psm_export_tsv_and_jsonl_are_stable() -> None:
    report = parse_psm_tsv(_psm_fixture("minimal_results.tsv"), mapping=_default_mapping())
    jsonl_path = _psm_fixture("normalized_again.jsonl")
    tsv_path = _psm_fixture("normalized_again.tsv")
    try:
        export_psm_jsonl(report.accepted_records, jsonl_path)
        export_psm_tsv(report.accepted_records, tsv_path)
        assert len(jsonl_path.read_text().strip().splitlines()) == 3
        assert tsv_path.read_text().splitlines()[0].startswith("spectrum_id\tpeptide")
    finally:
        jsonl_path.unlink(missing_ok=True)
        tsv_path.unlink(missing_ok=True)
