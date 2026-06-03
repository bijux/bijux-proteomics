# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification import (
    ConfidenceCalibrationLevel,
    FdrPolicy,
    ParsimonyVariant,
    PsmRecord,
    PsmSortField,
    PtmIdentificationObservation,
    SearchResultColumnMapping,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    apply_q_values,
    assign_confidence_labels,
    assign_level_specific_confidence_labels,
    assign_razor_peptides,
    build_accepted_psm_provenance_report,
    build_calibration_plot_data,
    build_combined_evidence_report,
    build_confidence_calibration_report,
    build_confidence_threshold_sensitivity_report,
    build_fdr_audit_trail,
    build_fdr_edge_case_report,
    build_grouped_confidence_report,
    build_inference_disagreement_report,
    build_peptide_protein_trace_report,
    build_peptide_summary_report,
    build_peptide_uniqueness_across_database,
    build_protein_coverage_map,
    build_protein_groups,
    build_protein_summary_report,
    build_psm_summary_report,
    build_razor_peptide_provenance_report,
    build_review_ready_evidence_bundle,
    build_search_result_provenance_manifest,
    build_shared_peptide_ambiguity_report,
    calculate_basic_target_decoy_fdr,
    calculate_grouped_fdr,
    calculate_level_specific_fdr,
    calculate_picked_protein_fdr,
    compare_parsimony_variants,
    compute_fdr_reproducibility_hash,
    detect_score_orientation_advisory,
    export_peptide_protein_trace_jsonl,
    export_peptide_protein_trace_tsv,
    export_psm_jsonl,
    export_psm_tsv,
    export_review_ready_evidence_bundle,
    filter_psms_by_fdr,
    infer_proteins_by_parsimony,
    normalize_psm_records,
    normalize_psm_score_orientation,
    parse_psm_tsv,
    parse_target_decoy_label,
    rollup_peptide_evidence,
    rollup_protein_evidence,
    select_best_psm_per_spectrum,
    sort_psm_records,
    validate_ptm_identification_confidence,
    validate_target_decoy_accession_collisions,
    validate_target_decoy_policy,
    verify_fdr_q_value_monotonicity,
)
from bijux_proteomics.identification.cross_run_reproducibility import (
    RunDetectionContext,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "psm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_psm_model_and_tsv_parser_accept_representative_fixture() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )

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


def test_psm_parser_populates_canonical_schema_fields(tmp_path: Path) -> None:
    source = tmp_path / "canonical_psm.tsv"
    source.write_text(
        "\n".join(
            (
                "run_name\tscan_ref\tsequence_text\tmodified_sequence\tz\tstate_score\tarea\tqvalue\taccessions\tdecoy_state\tcontaminant_state",
                "run_A\tgeneric-1001\tPESTIDE\tPES[Phospho]TIDE\t2\t55.0\t1200.5\t0.002\tP12345\ttarget\tfalse",
                "run_B\tgeneric-1002\tDECOYPEP\tDECOYPEP\t2\t12.0\t\t0.05\tCON__P54321\tdecoy\tcontaminant",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    mapping = SearchResultColumnMapping(
        run_id="run_name",
        spectrum_id="scan_ref",
        peptide="sequence_text",
        modified_peptide="modified_sequence",
        charge="z",
        score="state_score",
        intensity="area",
        q_value="qvalue",
        protein_refs="accessions",
        decoy_label="decoy_state",
        contaminant_label="contaminant_state",
    )

    report = parse_psm_tsv(source, mapping=mapping)

    assert len(report.accepted_records) == 2
    first = report.accepted_records[0]
    assert first.run_id == "run_A"
    assert first.peptide == "PESTIDE"
    assert first.peptide_sequence == "PESTIDE"
    assert first.modified_peptide == "PES[Phospho]TIDE"
    assert first.canonical_peptide == "PES[Phospho]TIDE"
    assert first.intensity == 1200.5
    assert first.contaminant_flag is False
    assert first.target_decoy_contaminant_class is TargetDecoyContaminantClass.TARGET
    second = report.accepted_records[1]
    assert second.run_id == "run_B"
    assert second.peptide_sequence == "DECOYPEP"
    assert second.modified_peptide is None
    assert second.intensity is None
    assert second.target_decoy_label is TargetDecoyLabel.DECOY
    assert second.contaminant_flag is True
    assert second.target_decoy_contaminant_class is TargetDecoyContaminantClass.MIXED


def test_psm_parser_preserves_engine_pep_without_relabeling_it_as_q_value(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pep_psm.tsv"
    source.write_text(
        "\n".join(
            (
                "scan_ref\tsequence_text\tz\tstate_score\tpep_value\taccessions",
                "pep-1001\tPEPTIDE\t2\t55.0\t0.002\tP12345",
                "pep-1002\tDECOYPEP\t2\t12.0\t0.12\tDECOY_P54321",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    mapping = SearchResultColumnMapping(
        spectrum_id="scan_ref",
        peptide="sequence_text",
        charge="z",
        score="state_score",
        posterior_error_probability="pep_value",
        protein_refs="accessions",
    )

    report = parse_psm_tsv(source, mapping=mapping)

    assert len(report.accepted_records) == 2
    first = report.accepted_records[0]
    assert first.posterior_error_probability == 0.002
    assert first.q_value is None
    second = report.accepted_records[1]
    assert second.posterior_error_probability == 0.12
    assert second.target_decoy_label is TargetDecoyLabel.DECOY


def test_psm_parser_accepts_csv_tables_through_shared_engine(tmp_path: Path) -> None:
    source = tmp_path / "comma_psm.csv"
    source.write_text(
        "\n".join(
            (
                "run_name,scan_ref,sequence_text,z,state_score,accessions",
                "run_A,generic-1001,PESTIDE,2,55.0,P12345",
                "run_B,generic-1002,DECOYPEP,3,12.0,DECOY_P54321",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    mapping = SearchResultColumnMapping(
        run_id="run_name",
        spectrum_id="scan_ref",
        peptide="sequence_text",
        charge="z",
        score="state_score",
        protein_refs="accessions",
    )

    report = parse_psm_tsv(source, mapping=mapping)

    assert len(report.accepted_records) == 2
    assert report.accepted_records[0].run_id == "run_A"
    assert report.accepted_records[1].target_decoy_label is TargetDecoyLabel.DECOY


def test_search_result_validation_rejects_missing_and_bad_fields() -> None:
    report = parse_psm_tsv(
        _psm_fixture("malformed_results.tsv"), mapping=_default_mapping()
    )

    assert len(report.accepted_records) == 0
    assert len(report.rejected_rows) == 4
    codes = {
        issue.code for rejected in report.rejected_rows for issue in rejected.issues
    }
    assert {
        "missing_spectrum_id",
        "missing_peptide",
        "invalid_charge",
        "invalid_score",
    } <= codes


def test_psm_parser_rejects_out_of_range_q_values(
    tmp_path: Path,
) -> None:
    source = tmp_path / "duplicate_psm.tsv"
    source.write_text(
        "\n".join(
            (
                "spectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins",
                "scan=1\tPEPTIDE\t2\t50\t0.01\tP1",
                "scan=2\tPEPTIDE\t2\t30\t1.2\tP2",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_psm_tsv(source, mapping=_default_mapping())

    assert len(report.accepted_records) == 1
    codes = {
        issue.code for rejected in report.rejected_rows for issue in rejected.issues
    }
    assert "invalid_q_value" in codes


def test_normalization_exports_stable_jsonl() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
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
    report = parse_psm_tsv(
        _psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping()
    )

    by_spectrum = sort_psm_records(report.accepted_records, by=PsmSortField.SPECTRUM)
    by_score = sort_psm_records(report.accepted_records, by=PsmSortField.SCORE)
    by_q_value = sort_psm_records(report.accepted_records, by=PsmSortField.Q_VALUE)
    by_peptide = sort_psm_records(report.accepted_records, by=PsmSortField.PEPTIDE)

    assert by_spectrum[0].spectrum_id == "scan=2001"
    assert by_score[0].score == 51.0
    assert by_q_value[0].q_value == 0.01
    assert by_peptide[0].canonical_peptide == "PEPTIDE"


def test_best_psm_per_spectrum_selector_prefers_highest_score() -> None:
    report = parse_psm_tsv(
        _psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping()
    )
    selected = select_best_psm_per_spectrum(report.accepted_records)

    assert len(selected) == 2
    best_scan_2001 = next(
        record for record in selected if record.spectrum_id == "scan=2001"
    )
    assert best_scan_2001.canonical_peptide == "PEPTIDER"
    assert best_scan_2001.score == 47.0


def test_peptide_level_rollup_combines_multiple_psms() -> None:
    report = parse_psm_tsv(
        _psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping()
    )
    rollups = rollup_peptide_evidence(report.accepted_records)

    assert len(rollups) == 2
    peptide_rollup = next(
        rollup for rollup in rollups if rollup.canonical_peptide == "PEPTIDER"
    )
    assert peptide_rollup.psm_count == 2
    assert peptide_rollup.spectrum_count == 2
    assert peptide_rollup.protein_refs == ("P12345", "Q11111")


def test_protein_level_evidence_rollup_counts_unique_and_shared_peptides() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
    rollups = rollup_protein_evidence(report.accepted_records)

    protein_rollup = next(
        rollup for rollup in rollups if rollup.protein_ref == "P12345"
    )
    shared_rollup = next(rollup for rollup in rollups if rollup.protein_ref == "Q22222")
    decoy_rollup = next(
        rollup for rollup in rollups if rollup.protein_ref == "DECOY_P99999"
    )

    assert protein_rollup.unique_peptide_count == 1
    assert protein_rollup.shared_peptide_count == 1
    assert shared_rollup.unique_peptide_count == 0
    assert decoy_rollup.target_decoy_label is TargetDecoyLabel.DECOY


def test_basic_target_decoy_fdr_and_q_values_are_monotonic() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    annotated = apply_q_values(report.accepted_records)

    assert all(record.q_value is not None for record in annotated)
    q_values = [record.q_value for record in annotated if record.q_value is not None]
    assert q_values == sorted(q_values)
    assert annotated[0].q_value == 0.0
    assert annotated[-1].q_value == 2 / 3


def test_basic_target_decoy_fdr_compatibility_surface_preserves_raw_counts() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())

    annotated = calculate_basic_target_decoy_fdr(report.accepted_records)

    assert annotated[0].cumulative_targets == 1
    assert annotated[0].cumulative_decoys == 0
    assert annotated[0].fdr == 0.0
    assert annotated[1].fdr == 1.0
    assert annotated[1].q_value == 0.5
    assert annotated[-1].q_value == 2 / 3


def test_tied_score_fdr_policy_is_explicit_and_reproducible() -> None:
    tied_records = (
        PsmRecord(
            spectrum_id="scan-a",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=50.0,
            protein_refs=("P1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-b",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=50.0,
            protein_refs=("DECOY_P2",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan-c",
            peptide="GLYGLYK",
            canonical_peptide="GLYGLYK",
            charge=2,
            score=40.0,
            protein_refs=("P3",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    grouped = apply_q_values(tied_records, tie_handling="score_group")
    ordered = apply_q_values(tied_records, tie_handling="stable_record_order")
    audit = build_fdr_audit_trail(tied_records, tie_handling="score_group")

    assert grouped[0].q_value == grouped[1].q_value
    assert ordered[0].q_value != ordered[1].q_value
    assert audit.policy.tie_handling == "score_group"
    assert audit.entries[0].tie_group_size == 2
    assert audit.entries[1].tie_group_rank == audit.entries[0].tie_group_rank


def test_fdr_threshold_filter_keeps_requested_cutoff() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.5)

    assert len(accepted) == 3
    strict = filter_psms_by_fdr(report.accepted_records, threshold=0.34)
    assert len(strict) == 1


def test_accepted_psm_provenance_report_tracks_rank_counts_threshold_and_transform() -> (
    None
):
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())

    provenance = build_accepted_psm_provenance_report(
        report.accepted_records,
        threshold=0.5,
        score_orientation="higher_better",
    )

    assert provenance.threshold == 0.5
    assert provenance.score_transform == "rank_normalized_psm_score"
    assert len(provenance.entries) == 3
    first = provenance.entries[0]
    assert first.rank == 1
    assert first.cumulative_targets == 1
    assert first.cumulative_decoys == 0
    assert first.score_orientation == "higher_better"
    assert first.normalized_score == 1.0


def test_score_orientation_normalization_supports_higher_and_lower_better() -> None:
    report = parse_psm_tsv(_psm_fixture("fdr_results.tsv"), mapping=_default_mapping())
    higher = normalize_psm_score_orientation(
        report.accepted_records, score_orientation="higher_better"
    )
    lower = normalize_psm_score_orientation(
        report.accepted_records, score_orientation="lower_better"
    )

    assert higher[0].raw_score == 100.0
    assert higher[0].normalized_score == 1.0
    assert lower[0].raw_score == 80.0
    assert lower[0].normalized_score == 1.0


def test_score_orientation_advisory_detection_stays_explicitly_advisory() -> None:
    lower_better_records = (
        PsmRecord(
            spectrum_id="scan-a",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=0.01,
            q_value=0.001,
            protein_refs=("P1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-b",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=0.02,
            q_value=0.002,
            protein_refs=("P2",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-c",
            peptide="DECA",
            canonical_peptide="DECA",
            charge=2,
            score=0.50,
            q_value=0.100,
            protein_refs=("DECOY_P3",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan-d",
            peptide="DECB",
            canonical_peptide="DECB",
            charge=2,
            score=0.60,
            q_value=0.200,
            protein_refs=("DECOY_P4",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )

    advisory = detect_score_orientation_advisory(lower_better_records, top_fraction=0.5)

    assert advisory.advisory_only is True
    assert advisory.recommended_orientation == "lower_better"
    assert advisory.support_gap > 0.0
    assert {candidate.orientation for candidate in advisory.candidates} == {
        "higher_better",
        "lower_better",
    }


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
    assert (
        sum(
            bin.target_count + bin.decoy_count + bin.mixed_count + bin.unknown_count
            for bin in calibration.bins
        )
        == 5
    )


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
    target_report = build_fdr_edge_case_report(no_decoys)
    decoy_report = build_fdr_edge_case_report(all_decoys)

    assert target_hash == repeated_hash
    assert target_hash != decoy_hash
    assert all(record.q_value == 1.0 for record in annotated_decoys)
    assert target_report.kind.value == "all_target"
    assert decoy_report.kind.value == "all_decoy"


def test_no_decoy_edge_case_report_is_distinct_from_all_target() -> None:
    no_decoy_records = (
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
            score=18.0,
            protein_refs=(),
            target_decoy_label=TargetDecoyLabel.UNKNOWN,
        ),
    )

    report = build_fdr_edge_case_report(no_decoy_records)

    assert report.kind.value == "no_decoy"
    assert report.decoy_count == 0
    assert report.unknown_count == 1


def test_target_decoy_accession_collisions_are_reported_and_refused() -> None:
    colliding_records = (
        PsmRecord(
            spectrum_id="scan-a",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=20.0,
            protein_refs=("P12345", "DECOY_P12345"),
            target_decoy_label=TargetDecoyLabel.MIXED,
        ),
    )

    collision_report = validate_target_decoy_accession_collisions(colliding_records)

    assert collision_report.valid is False
    assert collision_report.collisions[0].base_accession == "P12345"

    try:
        apply_q_values(colliding_records)
    except ValueError as exc:
        assert "target-decoy accession collision" in str(exc)
    else:
        raise AssertionError("expected target-decoy accession collision refusal")


def test_psm_summary_report_counts_labels_charges_and_score_bins() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
    summary = build_psm_summary_report(report.accepted_records)

    assert summary.total_psms == 3
    assert summary.target_psms == 2
    assert summary.decoy_psms == 1
    assert summary.counts_by_charge["2"] == 2


def test_peptide_summary_report_counts_modified_and_shared_peptides() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
    summary = build_peptide_summary_report(report.accepted_records)

    assert summary.total_peptides == 3
    assert summary.modified_peptides == 1
    assert summary.shared_peptides == 1


def test_protein_summary_report_supports_optional_coverage() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
    summary = build_protein_summary_report(
        report.accepted_records,
        protein_lengths={"P12345": 20, "Q22222": 20, "DECOY_P99999": 20},
    )

    first = next(
        group for group in summary.protein_groups if group.protein_ref == "P12345"
    )
    assert summary.total_proteins == 3
    assert first.coverage_fraction is not None
    assert 0.0 < first.coverage_fraction <= 1.0


def test_search_result_provenance_manifest_records_input_mapping_and_policy() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
    manifest = build_search_result_provenance_manifest(
        source_path=_psm_fixture("representative_results.tsv"),
        parse_report=report,
        decoy_policy=TargetDecoyLabelPolicy(),
        fdr_policy=FdrPolicy(threshold=0.01),
    )

    assert manifest.document_schema.document_kind == "search_result_provenance_manifest"
    assert manifest.source_sha256
    assert manifest.column_mapping.spectrum_id == "spectrum_id"
    assert manifest.fdr_policy is not None


def test_psm_export_tsv_and_jsonl_are_stable() -> None:
    report = parse_psm_tsv(
        _psm_fixture("representative_results.tsv"), mapping=_default_mapping()
    )
    jsonl_path = _psm_fixture("normalized_again.jsonl")
    tsv_path = _psm_fixture("normalized_again.tsv")
    try:
        export_psm_jsonl(report.accepted_records, jsonl_path)
        export_psm_tsv(report.accepted_records, tsv_path)
        assert len(jsonl_path.read_text().strip().splitlines()) == 3
        assert "intensity" in tsv_path.read_text().splitlines()[0]
    finally:
        jsonl_path.unlink(missing_ok=True)
        tsv_path.unlink(missing_ok=True)


def test_psm_parser_rejects_invalid_negative_intensity(tmp_path: Path) -> None:
    source = tmp_path / "invalid_intensity.tsv"
    source.write_text(
        "\n".join(
            (
                "spectrum_id\tpeptide\tcharge\tscore\tintensity\tproteins",
                "scan=1\tPEPTIDE\t2\t50.0\t-5\tP11111",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    mapping = SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        intensity="intensity",
        protein_refs="proteins",
    )

    report = parse_psm_tsv(source, mapping=mapping)

    assert len(report.accepted_records) == 0
    assert report.rejected_rows[0].issues[0].code == "invalid_intensity"


def test_level_specific_and_grouped_fdr_reports_cover_multiple_evidence_levels() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    level_report = calculate_level_specific_fdr(
        report.accepted_records,
        threshold=0.05,
        score_orientation="higher_better",
    )
    grouped_report = calculate_grouped_fdr(
        report.accepted_records,
        group_by="charge_state",
        threshold=0.05,
        score_orientation="higher_better",
    )

    assert len(level_report.psm_entries) == 5
    assert len(level_report.peptide_entries) == 5
    assert len(level_report.protein_entries) == 5
    assert len(grouped_report.groups) == 1
    assert grouped_report.groups[0].group_key == "z2"


def test_level_specific_peptide_fdr_collapses_duplicate_psms_into_one_peptide_entity() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping()
    )

    level_report = calculate_level_specific_fdr(
        report.accepted_records,
        threshold=0.05,
        score_orientation="higher_better",
    )

    assert len(level_report.peptide_entries) == 2
    peptide_entry = next(
        entry for entry in level_report.peptide_entries if entry.entity_id == "PEPTIDER"
    )
    assert peptide_entry.member_count == 2
    assert peptide_entry.protein_refs == ("P12345", "Q11111")


def test_level_specific_protein_fdr_uses_protein_entities_not_psm_rows() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=7001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=100.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=7002",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=95.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=7003",
            peptide="DECOYSEQ",
            canonical_peptide="DECOYSEQ",
            charge=2,
            score=80.0,
            protein_refs=("DECOY_P11111",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )

    level_report = calculate_level_specific_fdr(
        records,
        threshold=0.5,
        score_orientation="higher_better",
    )

    assert len(level_report.psm_entries) == 3
    assert len(level_report.protein_entries) == 2
    protein_entry = next(
        entry for entry in level_report.protein_entries if entry.entity_id == "P11111"
    )
    assert protein_entry.member_count == 2
    assert protein_entry.q_value == 0.0


def test_level_specific_confidence_labels_keep_evidence_levels_separate() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )

    confidence = assign_level_specific_confidence_labels(
        report.accepted_records,
        threshold=0.05,
        score_orientation="higher_better",
    )

    assert confidence.psm_assignments
    assert confidence.peptide_assignments
    assert confidence.protein_assignments
    assert {entry.evidence_level.value for entry in confidence.psm_assignments} == {
        "psm"
    }
    assert {entry.evidence_level.value for entry in confidence.peptide_assignments} == {
        "peptide"
    }
    assert {entry.evidence_level.value for entry in confidence.protein_assignments} == {
        "protein"
    }
    assert confidence.psm_assignments[0].entity_id.startswith("scan=")
    assert "GLYGLYK" in {entry.entity_id for entry in confidence.peptide_assignments}
    assert "P11111" in {entry.entity_id for entry in confidence.protein_assignments}


def test_fdr_monotonicity_verification_covers_supported_levels() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    monotonicity = verify_fdr_q_value_monotonicity(
        report.accepted_records,
        threshold=0.05,
        score_orientation="higher_better",
    )

    assert monotonicity.valid is True
    assert {check.scope for check in monotonicity.checks} >= {
        "psm",
        "peptide",
        "protein",
        "picked_protein",
    }
    assert all(check.first_break_rank is None for check in monotonicity.checks)


def test_protein_groups_parsimony_and_razor_assignments_are_stable() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)
    groups = build_protein_groups(accepted)
    parsimony = infer_proteins_by_parsimony(accepted)
    razor = assign_razor_peptides(accepted)

    indistinguishable = next(
        group for group in groups if group.protein_refs == ("P22222", "P44444")
    )
    shared_assignment = next(
        entry for entry in razor if entry.canonical_peptide == "SHAREDK"
    )

    assert indistinguishable.peptides == ("GLYGLYK", "SHAREDK")
    assert parsimony[0].protein_ref == "P11111"
    assert {entry.protein_ref for entry in parsimony} == {"P11111", "P22222", "P33333"}
    assert shared_assignment.assigned_protein == "P11111"
    assert shared_assignment.rationale == "unique_evidence_priority"


def test_razor_peptide_provenance_report_explains_assignment_policy() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    provenance = build_razor_peptide_provenance_report(accepted)

    shared = next(
        entry for entry in provenance.entries if entry.canonical_peptide == "SHAREDK"
    )
    assert provenance.policy_name == "unique_peptide_then_best_score_then_lexicographic"
    assert provenance.tie_break_order == (
        "unique_peptide_count",
        "best_score",
        "protein_accession",
    )
    assert shared.assigned_protein == "P11111"
    assert shared.candidate_unique_peptide_counts["P11111"] == 1
    assert shared.candidate_unique_peptide_counts["P22222"] == 0
    assert shared.candidate_best_scores["P11111"] == 100.0


def test_combined_evidence_report_joins_identification_ptm_and_quant_support() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    combined = build_combined_evidence_report(
        accepted,
        ptm_site_keys_by_peptide={
            "SHAREDK": ("P11111:S5:Phospho",),
        },
        quant_support_by_protein={
            "P11111": {"C1": 2200.0, "T1": 8100.0},
            "P22222": {"C1": 300.0},
        },
    )

    shared = next(
        entry
        for entry in combined.entries
        if entry.canonical_peptide == "SHAREDK" and entry.protein_ref == "P11111"
    )
    assert shared.psm_count == 1
    assert shared.protein_group_id is not None
    assert shared.ptm_site_keys == ("P11111:S5:Phospho",)
    assert shared.quant_support[0].sample_id == "C1"
    assert ParsimonyVariant.GREEDY_COVERAGE in shared.parsimony_variants


def test_confidence_calibration_report_adds_empirical_context_beyond_q_values() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )

    psm_calibration = build_confidence_calibration_report(
        report.accepted_records,
        score_orientation="higher_better",
    )
    protein_calibration = build_confidence_calibration_report(
        report.accepted_records,
        evidence_level=ConfidenceCalibrationLevel.PROTEIN,
        score_orientation="higher_better",
    )

    first_psm = psm_calibration.entries[0]
    assert first_psm.evidence_level.value == "psm"
    assert 0.0 <= first_psm.empirical_decoy_fraction <= 1.0
    assert 0.0 <= first_psm.support_score <= 1.0
    assert protein_calibration.evidence_level.value == "protein"
    assert any(entry.entity_id == "P11111" for entry in protein_calibration.entries)


def test_peptide_to_protein_trace_report_remains_stable_across_exports() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)
    trace = build_peptide_protein_trace_report(accepted)

    shared = next(
        entry for entry in trace.entries if entry.canonical_peptide == "SHAREDK"
    )
    assert shared.protein_refs == ("P11111", "P22222", "P44444")
    assert shared.protein_group_ids

    jsonl_path = _psm_fixture("peptide_protein_trace.jsonl")
    tsv_path = _psm_fixture("peptide_protein_trace.tsv")
    try:
        export_peptide_protein_trace_jsonl(trace, jsonl_path)
        export_peptide_protein_trace_tsv(trace, tsv_path)
        assert '"canonical_peptide":"SHAREDK"' in jsonl_path.read_text()
        assert (
            tsv_path.read_text()
            .splitlines()[0]
            .startswith("canonical_peptide\tpeptide\tspectrum_ids")
        )
    finally:
        jsonl_path.unlink(missing_ok=True)
        tsv_path.unlink(missing_ok=True)


def test_inference_disagreement_report_surfaces_strategy_divergence() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_parsimony_variants.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    disagreement = build_inference_disagreement_report(accepted)

    peptide_entry = next(
        entry for entry in disagreement.entries if entry.subject_id == "BRAVOK"
    )
    protein_set_entry = next(
        entry for entry in disagreement.entries if entry.kind.value == "protein_set"
    )
    assert peptide_entry.kind.value == "peptide_assignment"
    assert peptide_entry.strategy_assignments["razor"] == ("P20002",)
    assert (
        peptide_entry.strategy_assignments["parsimony:greedy_coverage"][0] == "P10001"
    )
    assert protein_set_entry.strategy_assignments["greedy_coverage"] == (
        "P10001",
        "P20002",
    )


def test_grouped_confidence_report_summarizes_indistinguishable_protein_groups() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    grouped = build_grouped_confidence_report(accepted)

    ambiguous = next(
        entry for entry in grouped.entries if entry.protein_refs == ("P22222", "P44444")
    )
    assert ambiguous.shared_peptide_count == 2
    assert ambiguous.unique_peptide_count == 0
    assert ambiguous.evidence_tier == "ambiguous"
    assert ambiguous.downgrade_reasons == ("shared_peptide_only",)
    assert ambiguous.confidence_label.value == "low"
    assert "supported only by shared peptides" in ambiguous.explanation


def test_grouped_confidence_report_keeps_one_weak_shared_peptide_from_strong_calls() -> (
    None
):
    grouped = build_grouped_confidence_report(
        (
            PsmRecord(
                spectrum_id="scan=1",
                peptide="SHAREDK",
                canonical_peptide="SHAREDK",
                charge=2,
                score=50.0,
                q_value=0.020,
                protein_refs=("P11111", "P22222"),
            ),
            PsmRecord(
                spectrum_id="scan=2",
                peptide="DECOYSEQ",
                canonical_peptide="DECOYSEQ",
                charge=2,
                score=55.0,
                q_value=0.010,
                protein_refs=("DECOY_P11111",),
                target_decoy_label=TargetDecoyLabel.DECOY,
            ),
        )
    )

    entry = next(
        candidate
        for candidate in grouped.entries
        if candidate.protein_refs == ("P11111", "P22222")
    )

    assert entry.protein_refs == ("P11111", "P22222")
    assert entry.shared_peptide_count == 1
    assert entry.evidence_tier == "ambiguous"
    assert entry.downgrade_reasons == ("shared_peptide_only",)
    assert entry.confidence_label.value == "low"


def test_grouped_confidence_report_downgrades_single_run_only_proteins() -> None:
    grouped = build_grouped_confidence_report(
        (
            PsmRecord(
                run_id="run-treated-1",
                spectrum_id="scan=1",
                peptide="SINGLERUN",
                canonical_peptide="SINGLERUN",
                charge=2,
                score=80.0,
                q_value=0.001,
                protein_refs=("P11111",),
            ),
            PsmRecord(
                run_id="run-control-1",
                spectrum_id="scan=2",
                peptide="DECOYSEQ",
                canonical_peptide="DECOYSEQ",
                charge=2,
                score=60.0,
                q_value=0.020,
                protein_refs=("DECOY_P11111",),
                target_decoy_label=TargetDecoyLabel.DECOY,
            ),
        ),
        run_contexts=(
            RunDetectionContext(
                run_id="run-control-1",
                sample_id="control-1",
                condition_id="control",
                replicate_id="1",
            ),
            RunDetectionContext(
                run_id="run-treated-1",
                sample_id="treated-1",
                condition_id="treated",
                replicate_id="1",
            ),
            RunDetectionContext(
                run_id="run-treated-2",
                sample_id="treated-2",
                condition_id="treated",
                replicate_id="2",
            ),
        ),
    )

    entry = next(
        candidate
        for candidate in grouped.entries
        if candidate.protein_refs == ("P11111",)
    )

    assert entry.evidence_tier == "moderate"
    assert entry.downgrade_reasons == ("single_run_only",)
    assert entry.confidence_label.value == "moderate"
    assert "observed in one run only" in entry.explanation


def test_grouped_confidence_report_preserves_explicit_exploratory_single_run_proteins() -> (
    None
):
    grouped = build_grouped_confidence_report(
        (
            PsmRecord(
                run_id="run-treated-1",
                spectrum_id="scan=1",
                peptide="EXPLORATORY",
                canonical_peptide="EXPLORATORY",
                charge=2,
                score=80.0,
                q_value=0.001,
                protein_refs=("P22222",),
            ),
            PsmRecord(
                run_id="run-control-1",
                spectrum_id="scan=2",
                peptide="DECOYSEQ",
                canonical_peptide="DECOYSEQ",
                charge=2,
                score=60.0,
                q_value=0.020,
                protein_refs=("DECOY_P11111",),
                target_decoy_label=TargetDecoyLabel.DECOY,
            ),
        ),
        run_contexts=(
            RunDetectionContext(
                run_id="run-control-1",
                sample_id="control-1",
                condition_id="control",
                replicate_id="1",
            ),
            RunDetectionContext(
                run_id="run-treated-1",
                sample_id="treated-1",
                condition_id="treated",
                replicate_id="1",
            ),
            RunDetectionContext(
                run_id="run-treated-2",
                sample_id="treated-2",
                condition_id="treated",
                replicate_id="2",
            ),
        ),
        exploratory_protein_refs=("P22222",),
    )

    entry = next(
        candidate
        for candidate in grouped.entries
        if candidate.protein_refs == ("P22222",)
    )

    assert entry.evidence_tier == "high_confidence"
    assert entry.downgrade_reasons == ()
    assert entry.confidence_label.value == "high"
    assert "high-confidence threshold" in entry.explanation


def test_custom_decoy_strategy_validation_reports_invalid_and_valid_policies() -> None:
    invalid = validate_target_decoy_policy(
        TargetDecoyLabelPolicy(
            explicit_decoy_values=("decoy", "target"),
            explicit_target_values=("target",),
        )
    )
    valid = validate_target_decoy_policy(
        TargetDecoyLabelPolicy(
            protein_suffix="_REV",
            explicit_decoy_values=("rev",),
            explicit_target_values=("target",),
        ),
        sample_protein_refs=("P11111", "P11111_REV"),
        sample_explicit_labels=("target", "rev"),
    )

    assert invalid.valid is False
    assert invalid.issues[0].code == "overlapping_explicit_values"
    assert valid.valid is True


def test_ptm_specific_identification_confidence_validation_is_explicit() -> None:
    report = validate_ptm_identification_confidence(
        (
            PtmIdentificationObservation(
                spectrum_id="scan=ptm-001",
                canonical_peptide="S[Phospho]PEPTIDEK",
                q_value=0.005,
                localization_score=0.99,
                candidate_site_count=1,
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PtmIdentificationObservation(
                spectrum_id="scan=ptm-005",
                canonical_peptide="AS[Phospho]TYK",
                q_value=0.02,
                localization_score=0.70,
                candidate_site_count=3,
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        )
    )

    confident = next(
        entry for entry in report.entries if entry.spectrum_id == "scan=ptm-001"
    )
    ambiguous = next(
        entry for entry in report.entries if entry.spectrum_id == "scan=ptm-005"
    )
    assert confident.valid is True
    assert ambiguous.valid is True
    assert {issue.code for issue in ambiguous.issues} == {
        "weak_localization_score",
        "ambiguous_site_localization",
    }


def test_review_ready_evidence_bundle_supports_downstream_review_exports() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)
    bundle = build_review_ready_evidence_bundle(
        accepted,
        threshold=0.05,
        score_orientation="higher_better",
        ptm_site_keys_by_peptide={"SHAREDK": ("P11111:S5:Phospho",)},
        quant_support_by_protein={"P11111": {"C1": 2200.0}},
    )

    assert bundle.document_schema.document_kind == "review_ready_evidence_bundle"
    assert bundle.psm_summary.total_psms == 4
    assert bundle.peptide_traces.entries
    assert bundle.combined_evidence.entries

    output_path = _psm_fixture("review_ready_evidence.json")
    try:
        export_review_ready_evidence_bundle(bundle, output_path)
        assert (
            json.loads(output_path.read_text())["document_schema"]["document_kind"]
            == "review_ready_evidence_bundle"
        )
    finally:
        output_path.unlink(missing_ok=True)


def test_named_parsimony_variants_are_explicit_and_comparable() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_parsimony_variants.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    greedy = infer_proteins_by_parsimony(
        accepted,
        variant=ParsimonyVariant.GREEDY_COVERAGE,
    )
    unique_first = infer_proteins_by_parsimony(
        accepted,
        variant=ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
    )
    comparison = compare_parsimony_variants(
        accepted,
        variants=(
            ParsimonyVariant.GREEDY_COVERAGE,
            ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ),
    )

    assert greedy[0].variant is ParsimonyVariant.GREEDY_COVERAGE
    assert greedy[0].protein_ref == "P10001"
    assert unique_first[0].variant is ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY
    assert unique_first[0].protein_ref == "P20002"
    difference = comparison.differences[0]
    assert difference.first_difference_rank == 1
    assert difference.shared_selected_proteins == ("P10001", "P20002")


def test_shared_peptide_ambiguity_report_explains_group_membership() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )

    ambiguity = build_shared_peptide_ambiguity_report(report.accepted_records)

    mixed_entry = next(
        entry
        for entry in ambiguity.entries
        if entry.protein_refs == ("P22222", "P44444")
    )
    assert mixed_entry.reason.value == "mixed"
    assert mixed_entry.shared_peptides == ("GLYGLYK", "SHAREDK")
    assert mixed_entry.outside_group_proteins == ("P11111",)


def test_grouped_and_picked_fdr_regression_fixture_covers_realistic_edge_cases() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("grouped_picked_fdr_edge_cases.tsv"), mapping=_default_mapping()
    )

    grouped_charge = calculate_grouped_fdr(
        report.accepted_records,
        group_by="charge_state",
        threshold=0.1,
        score_orientation="higher_better",
    )
    grouped_modification = calculate_grouped_fdr(
        report.accepted_records,
        group_by="modification_state",
        threshold=0.1,
        score_orientation="higher_better",
    )
    picked = calculate_picked_protein_fdr(
        report.accepted_records,
        threshold=0.1,
        score_orientation="higher_better",
    )

    assert {bucket.group_key for bucket in grouped_charge.groups} == {"z2", "z3", "z4"}
    assert {bucket.group_key for bucket in grouped_modification.groups} == {
        "modified",
        "unmodified",
    }
    assert {entry.protein_ref for entry in picked} == {
        "P11111",
        "P22222",
        "P33333",
        "P44444",
        "DECOY_P55555",
    }
    assert next(
        entry for entry in picked if entry.protein_ref == "P11111"
    ).partner_ref == ("DECOY_P11111")
    assert (
        next(
            entry for entry in picked if entry.protein_ref == "DECOY_P55555"
        ).partner_ref
        == "P55555"
    )
    assert "P55555" not in {entry.protein_ref for entry in picked}
    assert (
        next(entry for entry in picked if entry.protein_ref == "DECOY_P55555").accepted
        is False
    )
    assert [entry.q_value for entry in picked] == sorted(
        entry.q_value for entry in picked
    )


def test_confidence_threshold_sensitivity_report_tracks_incremental_acceptance() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("grouped_picked_fdr_edge_cases.tsv"), mapping=_default_mapping()
    )

    sensitivity = build_confidence_threshold_sensitivity_report(
        report.accepted_records,
        thresholds=(0.001, 0.01, 0.05, 0.1),
        score_orientation="higher_better",
    )

    assert sensitivity.thresholds == (0.001, 0.01, 0.05, 0.1)
    assert [entry.accepted_psm_count for entry in sensitivity.entries] == [5, 5, 5, 5]
    assert [entry.accepted_picked_protein_count for entry in sensitivity.entries] == [
        4,
        4,
        4,
        4,
    ]
    assert sensitivity.entries[0].newly_accepted_psm_ids == (
        "scan=8001",
        "scan=8002",
        "scan=8003",
        "scan=8004",
        "scan=8005",
    )
    assert sensitivity.entries[0].newly_accepted_picked_proteins == (
        "P11111",
        "P22222",
        "P33333",
        "P44444",
    )
    assert all(not entry.newly_accepted_psm_ids for entry in sensitivity.entries[1:])


def test_picked_protein_fdr_confidence_coverage_and_database_uniqueness_work_together() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)
    picked = calculate_picked_protein_fdr(accepted, threshold=0.05)
    confidence = assign_confidence_labels(
        picked, high_threshold=0.01, medium_threshold=0.05
    )
    fasta_report = parse_fasta_document(
        _fasta_fixture("protein_inference.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    coverage = build_protein_coverage_map(accepted, protein_sequences=protein_sequences)
    uniqueness = build_peptide_uniqueness_across_database(
        tuple(dict.fromkeys(record.canonical_peptide for record in accepted)),
        protein_sequences=protein_sequences,
    )

    assert {entry.protein_ref for entry in picked} == {
        "P11111",
        "P22222",
        "P33333",
        "P44444",
    }
    assert (
        next(entry for entry in confidence if entry.entity_id == "P11111").label.value
        == "high"
    )
    assert (
        next(
            entry for entry in coverage if entry.protein_ref == "P11111"
        ).coverage_fraction
        > 0.0
    )
    assert (
        next(
            entry for entry in uniqueness if entry.canonical_peptide == "SHAREDK"
        ).uniqueness.value
        == "shared"
    )
