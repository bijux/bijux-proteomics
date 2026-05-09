# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_public_packages import (
    build_flagship_dda_public_benchmark_package,
)
from bijux_proteomics.benchmarks.identification_pressure import (
    build_calibration_pressure_corpus_report,
    build_protein_inference_pressure_corpus_report,
)
from bijux_proteomics.identification.calibration_benchmarks import (
    AdapterCalibrationBenchmarkInput,
    build_adapter_calibration_benchmark_suite,
)
from bijux_proteomics.identification.confidence import ProteinInferenceStrategyKind
from bijux_proteomics.identification.contaminant_audit import (
    build_contaminant_aware_protein_inference_audit,
)
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_inference_benchmarks import (
    ProteinInferenceBenchmarkScenario,
    ProteinInferenceBenchmarkScenarioKind,
    build_identification_workflow_claim_review,
    build_protein_inference_benchmark_suite,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    normalize_search_results_with_adapter,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _adapter_input(
    adapter_kind: SearchAdapterKind,
    relative_path: str,
) -> AdapterCalibrationBenchmarkInput:
    normalization = normalize_search_results_with_adapter(
        source_path=_repo_root() / relative_path,
        adapter_kind=adapter_kind,
    )
    return AdapterCalibrationBenchmarkInput(
        adapter_kind=adapter_kind,
        records=normalization.normalized_records,
        score_orientation=normalization.adapter_manifest.score_orientation.value,
        entrapment_protein_refs=("ENTRAPMENT_P99999",),
    )


def _protein_inference_scenarios() -> tuple[ProteinInferenceBenchmarkScenario, ...]:
    return (
        ProteinInferenceBenchmarkScenario(
            scenario_id="shared-peptide-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY,
            records=(
                PsmRecord(
                    spectrum_id="s001",
                    peptide="UNIQUEP1",
                    canonical_peptide="UNIQUEP1",
                    charge=2,
                    score=120.0,
                    q_value=0.001,
                    protein_refs=("P11111",),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
                PsmRecord(
                    spectrum_id="s002",
                    peptide="SHAREDK",
                    canonical_peptide="SHAREDK",
                    charge=2,
                    score=115.0,
                    q_value=0.002,
                    protein_refs=("P11111", "P22222"),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
                PsmRecord(
                    spectrum_id="s003",
                    peptide="UNIQUEP3",
                    canonical_peptide="UNIQUEP3",
                    charge=2,
                    score=110.0,
                    q_value=0.003,
                    protein_refs=("P33333",),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
            ),
            expected_present_proteins=("P11111", "P33333"),
            expected_absent_proteins=("P22222",),
            note="Shared-peptide pressure keeps absent-protein promotion visible.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="isoform-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY,
            records=(
                PsmRecord(
                    spectrum_id="i001",
                    peptide="ISOFORM1K",
                    canonical_peptide="ISOFORM1K",
                    charge=2,
                    score=130.0,
                    q_value=0.001,
                    protein_refs=("P55555-1",),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
                PsmRecord(
                    spectrum_id="i002",
                    peptide="SHAREDISO",
                    canonical_peptide="SHAREDISO",
                    charge=2,
                    score=118.0,
                    q_value=0.002,
                    protein_refs=("P55555-1", "P55555-2"),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
            ),
            expected_present_proteins=("P55555-1",),
            expected_absent_proteins=("P55555-2",),
            note="Isoform-specific support should keep the silent sibling isoform out.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="false-negative-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.FALSE_NEGATIVE_PRESSURE,
            records=(
                PsmRecord(
                    spectrum_id="f001",
                    peptide="ANCHORP1",
                    canonical_peptide="ANCHORP1",
                    charge=2,
                    score=125.0,
                    q_value=0.001,
                    protein_refs=("P10101",),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
                PsmRecord(
                    spectrum_id="f002",
                    peptide="BRIDGEP",
                    canonical_peptide="BRIDGEP",
                    charge=2,
                    score=112.0,
                    q_value=0.003,
                    protein_refs=("P10101", "P20202"),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
            ),
            expected_present_proteins=("P10101", "P20202"),
            expected_absent_proteins=(),
            note="False-negative pressure stays visible for conservative strategies.",
        ),
    )


def test_calibration_pressure_corpus_report_tracks_real_adapter_family_identities() -> (
    None
):
    package = build_flagship_dda_public_benchmark_package()
    suite = build_adapter_calibration_benchmark_suite(
        (
            _adapter_input(
                SearchAdapterKind.MSFRAGGER,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
            ),
            _adapter_input(
                SearchAdapterKind.MAXQUANT_EVIDENCE,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
            ),
            _adapter_input(
                SearchAdapterKind.SPECTRONAUT,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
            ),
            _adapter_input(
                SearchAdapterKind.DIANN,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
            ),
        ),
        accepted_q_value_threshold=0.01,
        bin_count=5,
        top_fraction=0.2,
    )

    report = build_calibration_pressure_corpus_report(
        benchmark_package_id=package.package_id,
        imported_result_identity_paths=tuple(
            asset.path
            for asset in package.source_assets
            if asset.asset_role == "search_results"
        )
        + (
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
        ),
        benchmark_suite=suite,
    )

    assert report.benchmark_package_id == package.package_id
    assert report.adapter_family_count == 4
    assert {
        SearchAdapterKind.MSFRAGGER,
        SearchAdapterKind.MAXQUANT_EVIDENCE,
        SearchAdapterKind.SPECTRONAUT,
        SearchAdapterKind.DIANN,
    } == set(report.adapter_kinds)
    assert report.imported_result_identity_paths
    assert "public imported search-adapter results" in report.note


def test_protein_inference_pressure_corpus_report_keeps_contaminant_and_trust_pressure_visible() -> (
    None
):
    package = build_flagship_dda_public_benchmark_package()
    suite = build_protein_inference_benchmark_suite(_protein_inference_scenarios())
    claim_review = build_identification_workflow_claim_review(
        workflow_id="flagship-dda-identification",
        benchmark_suite=suite,
        material_loss_count=1,
        engine_disagreement_count=1,
        contaminant_risk=True,
        calibration_release_blocked=True,
    )
    contaminant_audit = build_contaminant_aware_protein_inference_audit(
        (
            PsmRecord(
                spectrum_id="c001",
                peptide="UNIQUEC",
                canonical_peptide="UNIQUEC",
                charge=2,
                score=120.0,
                q_value=0.001,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="c002",
                peptide="CONTAMK",
                canonical_peptide="CONTAMK",
                charge=2,
                score=118.0,
                q_value=0.002,
                protein_refs=("CON__KERATIN1", "P11111"),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        )
    )

    report = build_protein_inference_pressure_corpus_report(
        benchmark_package_id=package.package_id,
        supporting_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/psm/protein_inference_results.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/fasta/protein_inference.fasta",
        ),
        benchmark_suite=suite,
        claim_review=claim_review,
        contaminant_audit=contaminant_audit,
    )

    assert report.shared_peptide_pressure_scenario_count == 1
    assert report.isoform_pressure_scenario_count == 1
    assert report.false_negative_pressure_scenario_count == 1
    assert report.unresolved_contaminant_promotion is True
    assert report.ready_for_broad_identification_claim is False
    assert (
        ProteinInferenceStrategyKind.PARSIMONY
        in report.benchmark_suite.covered_strategy_kinds
    )
