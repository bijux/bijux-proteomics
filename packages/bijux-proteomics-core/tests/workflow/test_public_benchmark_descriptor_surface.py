# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from bijux_proteomics.domain.errors import (
    DesignError,
    InvalidWorkflowError,
    SchemaError,
)
from bijux_proteomics.workflow import (
    PublicBenchmarkExpectedSignalAssessmentStatus,
    PublicBenchmarkFailureKind,
    PublicBenchmarkKnownLimitationSeverity,
    PublicBenchmarkSearchEngine,
    load_public_benchmark_descriptor,
    public_benchmark_root,
    render_public_benchmark_suite_signal_assessments_tsv,
    resolve_public_benchmark_path,
    resolve_public_benchmark_root,
    run_public_benchmark_descriptor,
    run_public_benchmark_descriptor_suite,
)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_descriptor_copy(
    tmp_path: Path,
    source_name: str,
    *,
    mutate: Callable[[dict], None] | None = None,
) -> Path:
    source_path = public_benchmark_root() / source_name / "dataset.yml"
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(payload)
    target_dir = tmp_path / source_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "dataset.yml"
    target_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return target_path


def _rewrite_descriptor_source(
    payload: dict,
    *,
    schema_id: str,
    path: Path,
) -> None:
    for source in payload["source_files"]:
        if source["schema_id"] == schema_id:
            source["repo_relative_path"] = str(path)
            source["sha256"] = _sha256(path)
            return
    raise AssertionError(f"missing schema_id {schema_id!r}")


def _write_clean_targeted_results(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality",
                "P001\tPEPTIDEK\t2\t445.2\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass",
                "P001\tPEPTIDEK\t2\t445.2\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass",
                "P002\tACDMPEP\t3\t512.3\ty5\t602.3\tcontrol_r1\t93000\t18.40\tpass",
                "P002\tACDMPEP\t3\t512.3\ty6\t715.4\tcontrol_r1\t87000\t18.47\tpass",
                "P002\tACDMPEP\t3\t512.3\ty5\t602.3\tcontrol_r2\t92000\t18.41\tpass",
                "P002\tACDMPEP\t3\t512.3\ty6\t715.4\tcontrol_r2\t86000\t18.48\tpass",
                "P002\tACDMPEP\t3\t512.3\ty5\t602.3\ttreat_r1\t43000\t18.42\tpass",
                "P002\tACDMPEP\t3\t512.3\ty6\t715.4\ttreat_r1\t39000\t18.46\tpass",
                "P002\tACDMPEP\t3\t512.3\ty5\t602.3\ttreat_r2\t42000\t18.40\tpass",
                "P002\tACDMPEP\t3\t512.3\ty6\t715.4\ttreat_r2\t38500\t18.45\tpass",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_public_benchmark_descriptor_loads_real_sample_metadata_signal_and_limitation_contracts() -> (
    None
):
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "ptm_localization_review_package" / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.PTM
    assert descriptor.expected_input_schemas == (
        "evidence_tsv",
        "feature_tsv",
        "proteins_fasta",
        "design_tsv",
        "annotation_tsv",
    )
    assert len(descriptor.sample_metadata) == 4
    assert descriptor.expected_biological_signals[0].subject_id == "P11111:S5:Phospho"
    assert descriptor.expected_approximate_counts[2].metric_id == "ambiguous_site_count"
    assert (
        descriptor.expected_approximate_counts[3].metric_id
        == "ambiguous_group_row_count"
    )
    assert descriptor.known_limitations[0].severity is (
        PublicBenchmarkKnownLimitationSeverity.ADVISORY
    )
    assert descriptor.command.parameters["annotation_target_species"] == "Homo sapiens"


def test_public_benchmark_descriptor_resolves_package_owned_root_aliases() -> None:
    package_root = public_benchmark_root()

    assert resolve_public_benchmark_root() == package_root
    assert resolve_public_benchmark_root(Path("benchmarks/public")) == package_root
    assert resolve_public_benchmark_root(Path("./benchmarks/public")) == package_root
    assert resolve_public_benchmark_path(
        Path("benchmarks/public/ptm_localization_review_package/dataset.yml")
    ) == (package_root / "ptm_localization_review_package" / "dataset.yml")


def test_public_benchmark_descriptor_rejects_duplicate_source_ids_with_schema_error(
    tmp_path: Path,
) -> None:
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "ptm_localization_review_package",
        mutate=lambda payload: payload["source_files"].append(
            dict(payload["source_files"][0])
        ),
    )

    with pytest.raises(SchemaError, match="descriptor source_ids must be unique"):
        load_public_benchmark_descriptor(descriptor_path)


def test_public_benchmark_descriptor_rejects_misaligned_sample_group_design(
    tmp_path: Path,
) -> None:
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "ptm_localization_review_package",
        mutate=lambda payload: payload["sample_groups"][0].update(
            sample_ids=["sample-a", "sample-b", "sample-extra"]
        ),
    )

    with pytest.raises(
        DesignError,
        match="descriptor sample_groups and sample_metadata must declare the same sample_ids",
    ):
        load_public_benchmark_descriptor(descriptor_path)


def test_public_benchmark_root_rejects_descriptor_paths_as_invalid_workflow_input() -> (
    None
):
    descriptor_path = (
        public_benchmark_root() / "ptm_localization_review_package" / "dataset.yml"
    )

    with pytest.raises(
        InvalidWorkflowError,
        match="public benchmark root must be a directory",
    ):
        resolve_public_benchmark_root(descriptor_path)


def test_public_benchmark_descriptor_loads_runnable_diann_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "dia_diann_benchmark_dataset" / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.DIANN
    assert descriptor.expected_input_schemas == (
        "result_tsv",
        "config_json",
        "design_tsv",
        "proteins_fasta",
    )
    assert len(descriptor.sample_metadata) == 6
    assert descriptor.expected_biological_signals[0].subject_id == "P04637"


def test_public_benchmark_descriptor_loads_runnable_maxquant_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "maxquant_lfq_benchmark_dataset" / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.MAXQUANT
    assert descriptor.expected_input_schemas == (
        "evidence_txt",
        "peptides_txt",
        "protein_groups_txt",
        "design_tsv",
        "proteins_fasta",
    )
    assert len(descriptor.sample_metadata) == 6
    assert descriptor.expected_biological_signals[0].subject_id == "P04637"


def test_public_benchmark_descriptor_loads_runnable_fragpipe_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "fragpipe_msfragger_benchmark_dataset" / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.FRAGPIPE
    assert descriptor.expected_input_schemas == (
        "search_result_tsv",
        "source_protein_tsv",
        "design_tsv",
        "proteins_fasta",
    )
    assert len(descriptor.sample_metadata) == 6
    assert descriptor.expected_biological_signals[0].subject_id == "P04637"


def test_public_benchmark_descriptor_loads_runnable_tmt_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "multiplex_tmtpro_review_package" / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.TMT
    assert descriptor.expected_input_schemas == ("result_tsv", "design_tsv")
    assert len(descriptor.sample_metadata) == 8
    assert descriptor.expected_approximate_counts[-1].metric_id == (
        "flagged_interference_count"
    )
    assert descriptor.known_limitations[0].severity is (
        PublicBenchmarkKnownLimitationSeverity.ADVISORY
    )


def test_public_benchmark_descriptor_loads_runnable_targeted_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "targeted_transition_review_package" / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.TARGETED
    assert descriptor.expected_input_schemas == (
        "input_tsv",
        "design_tsv",
        "discovery_claims_json",
        "panel_assays_json",
    )
    assert len(descriptor.sample_metadata) == 4
    assert descriptor.command.parameters["stage"] == "validation"
    assert descriptor.expected_approximate_counts[-1].metric_id == "inconclusive_count"
    assert descriptor.known_limitations[0].severity is (
        PublicBenchmarkKnownLimitationSeverity.ADVISORY
    )


def test_public_benchmark_descriptor_loads_weak_evidence_lfq_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root()
        / "lfq_sparse_contrast_benchmark_dataset"
        / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.LFQ
    assert descriptor.expected_input_schemas == (
        "input_tsv",
        "design_tsv",
        "proteins_fasta",
    )
    assert len(descriptor.sample_metadata) == 5
    assert descriptor.expected_approximate_counts[1].metric_id == (
        "significant_protein_count"
    )
    assert descriptor.known_limitations[0].severity is (
        PublicBenchmarkKnownLimitationSeverity.ADVISORY
    )


def test_public_benchmark_runner_validates_expected_signal_assessments_for_real_ptm_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root() / "ptm_localization_review_package" / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert len(report.expected_signal_assessments) == 2
    assert report.verified_counts["ambiguous_site_count"] == 2
    assert report.verified_counts["ambiguous_group_row_count"] == 2
    assert report.verified_counts["motif_term_count"] == 22
    assert report.verified_counts["evidence_card_count"] == 3
    assert {assessment.status for assessment in report.expected_signal_assessments} == {
        PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED
    }
    assert Path(report.output_dir, "ptm_regulator_enrichment_summary.tsv").exists()
    assert Path(report.output_dir, "ptm_regulator_enrichment.tsv").exists()
    assert Path(report.output_dir, "ptm_evidence_cards.tsv").exists()
    assert Path(report.output_dir, "ptm_site_group_summary.tsv").exists()
    assert Path(report.output_dir, "ptm_site_group_matrix.tsv").exists()
    assert Path(report.output_dir, "ptm_site_group_missingness.tsv").exists()


def test_public_benchmark_runner_executes_runnable_maxquant_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root() / "maxquant_lfq_benchmark_dataset" / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["imported_evidence_count"] == 8
    assert report.verified_counts["accepted_protein_group_count"] == 5
    assert {assessment.status for assessment in report.expected_signal_assessments} == {
        PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED
    }
    assert Path(report.output_dir, "maxquant_lfq_matrix.tsv").exists()
    assert Path(report.output_dir, "maxquant_filtered_protein_groups.tsv").exists()


def test_public_benchmark_runner_executes_runnable_fragpipe_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root()
        / "fragpipe_msfragger_benchmark_dataset"
        / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["accepted_psm_count"] == 30
    assert report.verified_counts["protein_group_discrepancy_count"] == 2
    assert {assessment.status for assessment in report.expected_signal_assessments} == {
        PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED
    }
    assert Path(report.output_dir, "dda_biological_psms.tsv").exists()
    assert Path(report.output_dir, "dda_source_protein_discrepancies.tsv").exists()


def test_public_benchmark_runner_executes_runnable_diann_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root() / "dia_diann_benchmark_dataset" / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["imported_precursor_count"] == 31
    assert report.verified_counts["protein_matrix_row_count"] == 5
    assert {assessment.status for assessment in report.expected_signal_assessments} == {
        PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED
    }
    assert Path(report.output_dir, "diann_precursor_quantity_matrix.tsv").exists()
    assert Path(report.output_dir, "diann_import_rejected_evidence.tsv").exists()


def test_public_benchmark_runner_executes_runnable_tmt_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root() / "multiplex_tmtpro_review_package" / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["accepted_input_row_count"] == 4
    assert report.verified_counts["protein_ratio_count"] == 12
    assert report.verified_counts["interference_observation_count"] == 12
    assert report.verified_counts["flagged_interference_count"] == 6
    assert not report.expected_signal_assessments
    assert Path(report.output_dir, "tmt_validation_summary.tsv").exists()
    assert Path(report.output_dir, "tmt_normalization_summary.tsv").exists()


def test_public_benchmark_runner_executes_runnable_targeted_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root() / "targeted_transition_review_package" / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["target_count"] == 2
    assert report.verified_counts["flagged_coelution_target_entry_count"] == 3
    assert report.verified_counts["unreliable_target_count"] == 2
    assert report.verified_counts["discovery_claim_count"] == 2
    assert report.verified_counts["inconclusive_count"] == 2
    assert not report.expected_signal_assessments
    assert Path(report.output_dir, "advanced_targeted_workflow_manifest.json").exists()
    assert Path(report.output_dir, "targeted_assay_qc_summary.tsv").exists()
    assert Path(report.output_dir, "targeted_matrix_summary.tsv").exists()
    assert Path(report.output_dir, "targeted_assay_qc_unreliable_targets.tsv").exists()
    assert Path(report.output_dir, "targeted_assay_qc_fragment_ratios.tsv").exists()
    assert Path(report.output_dir, "targeted_assay_qc_transition_qc.tsv").exists()
    assert Path(report.output_dir, "targeted_validation_summary.tsv").exists()
    assert Path(report.output_dir, "targeted_validation_inconclusive.tsv").exists()
    assert Path(report.output_dir, "targeted_validation_evidence.tsv").exists()


def test_public_benchmark_runner_fails_targeted_descriptor_without_unreliable_evidence(
    tmp_path: Path,
) -> None:
    clean_results = tmp_path / "clean_targeted_results.tsv"
    _write_clean_targeted_results(clean_results)
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "targeted_transition_review_package",
        mutate=lambda payload: _rewrite_descriptor_source(
            payload,
            schema_id="input_tsv",
            path=clean_results,
        ),
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.APPROXIMATE_COUNT_MISMATCH
        and failure.subject == "unreliable_target_count"
        for failure in report.failures
    )


def test_public_benchmark_runner_executes_weak_evidence_lfq_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        public_benchmark_root()
        / "lfq_sparse_contrast_benchmark_dataset"
        / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["protein_count"] == 4
    assert report.verified_counts["significant_protein_count"] == 0
    assert report.verified_counts["warning_card_count"] == 4
    assert report.verified_counts["cohort_blocked_stratum_count"] == 2
    assert report.verified_counts["weak_confidence_section_count"] == 2
    assert report.verified_counts["invalid_section_count"] == 11
    assert not report.expected_signal_assessments
    assert Path(report.output_dir, "biological_rejected_claims.tsv").exists()
    assert Path(report.output_dir, "biological_report_section_confidence.tsv").exists()
    assert Path(
        report.output_dir, "biological_cohort_stratification_summary.tsv"
    ).exists()


def test_public_benchmark_runner_fails_when_descriptor_sample_metadata_conflicts_with_design(
    tmp_path: Path,
) -> None:
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "lfq_cohort_review_package",
        mutate=lambda payload: payload["sample_metadata"][0].update(
            {"batch": "batch-z"}
        ),
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.SAMPLE_METADATA_MISMATCH
        for failure in report.failures
    )


def test_public_benchmark_runner_blocks_tmt_descriptor_with_missing_channel_mapping(
    tmp_path: Path,
) -> None:
    missing_design = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "multiplex"
        / "tmt_missing_channel.design.tsv"
    )
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "multiplex_tmtpro_review_package",
        mutate=lambda payload: _rewrite_descriptor_source(
            payload,
            schema_id="design_tsv",
            path=missing_design,
        ),
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.MULTIPLEX_CHANNEL_MAPPING_INVALID
        and failure.subject == "missing_channel_assignment"
        for failure in report.failures
    )


def test_public_benchmark_runner_fails_when_declared_signal_direction_is_not_observed(
    tmp_path: Path,
) -> None:
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "ptm_localization_review_package",
        mutate=lambda payload: payload["expected_biological_signals"][0].update(
            {"expected_direction": "down"}
        ),
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.EXPECTED_SIGNAL_MISMATCH
        for failure in report.failures
    )
    assert any(
        assessment.status is PublicBenchmarkExpectedSignalAssessmentStatus.MISMATCHED
        for assessment in report.expected_signal_assessments
    )


def test_public_benchmark_runner_renders_signal_assessment_ledger(
    tmp_path: Path,
) -> None:
    suite = run_public_benchmark_descriptor_suite(
        public_benchmark_root(),
        output_root=tmp_path / "runs",
    )

    signal_tsv = render_public_benchmark_suite_signal_assessments_tsv(suite)

    assert signal_tsv.splitlines()[0] == (
        "dataset_id\taccession\tstatus\tsignal_id\tsubject_kind\tsubject_id\t"
        "expected_direction\tassessment_status\tsource_surface\tobserved_direction\t"
        "observed_effect_size\tobserved_adjusted_p_value\tnote"
    )
    assert "ptm_site_p11111_s5_up" in signal_tsv
    assert "dia_sig_a_up" in signal_tsv
    assert "maxquant_sig_a_up" in signal_tsv
    assert "fragpipe_sig_a_up" in signal_tsv
