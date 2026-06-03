# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.dia_targeted_pressure import (
    build_dia_pressure_corpus_report,
    build_targeted_pressure_corpus_report,
)
from bijux_proteomics.benchmarks.flagship_public_packages import (
    build_flagship_dda_public_benchmark_package,
    build_flagship_lfq_public_benchmark_package,
    build_flagship_ptm_public_benchmark_package,
)
from bijux_proteomics.benchmarks.identification_pressure import (
    build_calibration_pressure_corpus_report,
    build_protein_inference_pressure_corpus_report,
)
from bijux_proteomics.benchmarks.ptm_pressure import build_ptm_pressure_corpus_report
from bijux_proteomics.benchmarks.quantification_pressure import (
    build_quantification_pressure_corpus_report,
)
from bijux_proteomics.dia.benchmarks import (
    TargetedCalibrationStandardObservation,
    TargetedHandoffHonestyObservation,
    TargetedHeavyLightPairObservation,
    TargetedOutcomeReconciliationObservation,
    build_dia_workflow_scientific_support_report,
    build_targeted_raw_to_reviewed_bundle_report,
    build_targeted_workflow_benchmark_report,
)
from bijux_proteomics.identification.calibration_benchmarks import (
    AdapterCalibrationBenchmarkInput,
    build_adapter_calibration_benchmark_suite,
)
from bijux_proteomics.identification.contaminant_audit import (
    build_contaminant_aware_protein_inference_audit,
)
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_inference_benchmarks import (
    ProteinInferenceBenchmarkScenario,
    build_core_protein_inference_benchmark_scenarios,
    build_identification_workflow_claim_review,
    build_protein_inference_benchmark_suite,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    normalize_search_results_with_adapter,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    build_ptm_ambiguity_propagation_benchmark_report,
    build_ptm_family_credibility_track_report,
    build_ptm_lab_targeting_rubric_report,
    build_ptm_localization_confidence_benchmark_report,
    build_ptm_occupancy_stress_benchmark_report,
    build_ptm_raw_spectrum_validation_lane_report,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.quantification.benchmarks import (
    build_effect_size_stability_benchmark_report,
    build_quant_missingness_robustness_report,
    build_quant_normalization_impact_benchmark_report,
)
from bijux_proteomics.review.scientific_failure_atlas import (
    ScientificFailureSeverity,
    build_scientific_failure_atlas_report,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


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


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _protein_inference_scenarios() -> tuple[ProteinInferenceBenchmarkScenario, ...]:
    return build_core_protein_inference_benchmark_scenarios()


def test_scientific_failure_atlas_report_gathers_cross_family_blockers() -> None:
    dda_package = build_flagship_dda_public_benchmark_package()
    lfq_package = build_flagship_lfq_public_benchmark_package()
    ptm_package = build_flagship_ptm_public_benchmark_package()

    calibration_suite = build_adapter_calibration_benchmark_suite(
        (
            _adapter_input(
                SearchAdapterKind.MSFRAGGER,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
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
    calibration_pressure = build_calibration_pressure_corpus_report(
        benchmark_package_id=dda_package.package_id,
        imported_result_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
        ),
        benchmark_suite=calibration_suite,
    )
    protein_suite = build_protein_inference_benchmark_suite(
        _protein_inference_scenarios()
    )
    protein_claim_review = build_identification_workflow_claim_review(
        workflow_id="flagship-dda-identification",
        benchmark_suite=protein_suite,
        material_loss_count=1,
        engine_disagreement_count=1,
        contaminant_risk=True,
        calibration_release_blocked=True,
    )
    contaminant_audit = build_contaminant_aware_protein_inference_audit(
        (
            PsmRecord(
                spectrum_id="c001",
                peptide="ACDEFGK",
                canonical_peptide="ACDEFGK",
                charge=2,
                score=120.0,
                q_value=0.001,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="c002",
                peptide="KERATIN",
                canonical_peptide="KERATIN",
                charge=2,
                score=118.0,
                q_value=0.002,
                protein_refs=("CON__KERATIN1", "P11111"),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        )
    )
    protein_pressure = build_protein_inference_pressure_corpus_report(
        benchmark_package_id=dda_package.package_id,
        supporting_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/psm/protein_inference_results.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/fasta/protein_inference.fasta",
        ),
        benchmark_suite=protein_suite,
        claim_review=protein_claim_review,
        contaminant_audit=contaminant_audit,
    )

    quant_records = parse_ms1_feature_table(
        _quant_fixture("study_scale_ms1_features.tsv")
    ).accepted_records
    quant_design = parse_experimental_design_table(
        _quant_fixture("study_scale.design.tsv")
    ).accepted_entries
    quant_missingness = build_quant_missingness_robustness_report(
        quant_records,
        design_entries=quant_design,
    )
    quant_normalization = build_quant_normalization_impact_benchmark_report(
        quant_records,
        design_entries=quant_design,
        condition_a="control",
        condition_b="treatment",
    )
    quant_effect_size = build_effect_size_stability_benchmark_report(
        quant_records,
        tuple(
            record.model_copy(
                update={
                    "intensity": (
                        round(record.intensity * 1.01, 6)
                        if record.intensity is not None
                        and record.sample_id.startswith("T")
                        else record.intensity
                    )
                }
            )
            for record in quant_records
        ),
        design_entries=quant_design,
        condition_a="control",
        condition_b="treatment",
    )
    quant_pressure = build_quantification_pressure_corpus_report(
        benchmark_package_id=lfq_package.package_id,
        supporting_identity_paths=tuple(
            asset.path for asset in lfq_package.source_assets
        ),
        missingness_robustness=quant_missingness,
        normalization_impact=quant_normalization,
        effect_size_stability=quant_effect_size,
    )

    parsed = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    ptm_sites = build_ptm_site_table(mappings)
    ptm_features = parse_ms1_feature_table(
        _ptm_fixture("ptm_features.tsv")
    ).accepted_records
    ptm_pressure = build_ptm_pressure_corpus_report(
        benchmark_package_id=ptm_package.package_id,
        supporting_identity_paths=tuple(
            asset.path for asset in ptm_package.source_assets
        ),
        localization_confidence=build_ptm_localization_confidence_benchmark_report(
            parsed.accepted_records,
            mappings,
            fragment_ion_support_by_spectrum={
                "scan=ptm-001": ("b5", "y6", "y7"),
                "scan=ptm-002": ("b4",),
            },
        ),
        ambiguity_propagation=build_ptm_ambiguity_propagation_benchmark_report(
            ptm_sites,
            feature_records=ptm_features,
        ),
        occupancy_stress=build_ptm_occupancy_stress_benchmark_report(
            ptm_sites,
            baseline_feature_records=ptm_features,
            stressed_feature_records=tuple(
                row
                for row in ptm_features
                if not (row.sample_id == "T2" and row.intensity is not None)
            ),
        ),
        raw_spectrum_validation=build_ptm_raw_spectrum_validation_lane_report(
            parsed.accepted_records,
            raw_spectrum_artifact_path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
            fragment_ion_support_by_spectrum={
                "scan=ptm-001": ("b5", "y6"),
            },
        ),
        family_credibility=build_ptm_family_credibility_track_report(
            ptm_sites,
            feature_records=ptm_features,
            protein_sequences=_protein_sequences(),
        ),
        lab_targeting=build_ptm_lab_targeting_rubric_report(
            parsed.accepted_records,
            mappings,
            ptm_sites,
            feature_records=ptm_features,
        ),
    )

    dia_pressure = build_dia_pressure_corpus_report(
        benchmark_surface_id="reviewable_import_surface:dia_library_conditioned_bundle",
        supporting_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/formats/ion_mobility.mzml",
        ),
        support_report=build_dia_workflow_scientific_support_report(
            imported_precursor_count=92,
            expected_precursor_count=100,
            sample_resolved_precursor_count=88,
            expected_sample_resolved_precursor_count=100,
            transition_supported_precursor_count=73,
            expected_transition_precursor_count=100,
            protein_group_count=61,
            expected_protein_group_count=100,
            sample_resolved_protein_count=58,
            expected_sample_resolved_protein_count=100,
            ion_mobility_observed_count=54,
            ion_mobility_expected_count=100,
            library_matched_peptide_count=81,
            expected_library_peptide_count=100,
            absent_expected_peptide_count=19,
        ),
    )
    targeted_benchmark = build_targeted_workflow_benchmark_report(
        calibration_observations=(
            TargetedCalibrationStandardObservation(
                standard_id="std-a",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=0.97,
                within_tolerance=True,
            ),
            TargetedCalibrationStandardObservation(
                standard_id="std-b",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=1.34,
                within_tolerance=False,
            ),
        ),
        heavy_light_pairs=(
            TargetedHeavyLightPairObservation(
                pair_id="pair-a",
                light_candidate_id="pep-a-light",
                heavy_candidate_id="pep-a-heavy",
                pair_complete=True,
                heavy_light_ratio=1.02,
                interference_fraction=0.08,
            ),
            TargetedHeavyLightPairObservation(
                pair_id="pair-b",
                light_candidate_id="pep-b-light",
                heavy_candidate_id="pep-b-heavy",
                pair_complete=False,
                interference_fraction=0.22,
            ),
        ),
    )
    targeted_pressure = build_targeted_pressure_corpus_report(
        benchmark_surface_id="reviewable_import_surface:targeted_transition_bundle",
        supporting_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
        ),
        workflow_benchmark=targeted_benchmark,
        raw_to_reviewed_bundle=build_targeted_raw_to_reviewed_bundle_report(
            chromatogram_failed_metric_rows=0,
            benchmark_report=targeted_benchmark,
            handoff_observations=(
                TargetedHandoffHonestyObservation(
                    handoff_id="handoff-a",
                    claimed_transition_ready=True,
                    calibration_failures_visible=True,
                    interference_failures_visible=True,
                    control_gaps_visible=True,
                ),
                TargetedHandoffHonestyObservation(
                    handoff_id="handoff-b",
                    claimed_transition_ready=True,
                    calibration_failures_visible=False,
                    interference_failures_visible=True,
                    control_gaps_visible=True,
                ),
            ),
            outcome_observations=(
                TargetedOutcomeReconciliationObservation(
                    handoff_id="handoff-a",
                    observed_transition_failure=False,
                    reconciliation_recorded=False,
                    corrective_action_visible=False,
                ),
                TargetedOutcomeReconciliationObservation(
                    handoff_id="handoff-b",
                    observed_transition_failure=True,
                    reconciliation_recorded=False,
                    corrective_action_visible=False,
                ),
            ),
        ),
    )

    atlas = build_scientific_failure_atlas_report(
        dda_package=dda_package,
        lfq_package=lfq_package,
        ptm_package=ptm_package,
        calibration_pressure=calibration_pressure,
        protein_inference_pressure=protein_pressure,
        quantification_pressure=quant_pressure,
        ptm_pressure=ptm_pressure,
        dia_pressure=dia_pressure,
        targeted_pressure=targeted_pressure,
    )

    assert {entry.workflow_family for entry in atlas.entries} == {
        "identification",
        "quantification",
        "ptm",
        "dia",
        "targeted",
    }
    assert any(
        entry.severity is ScientificFailureSeverity.HIGH for entry in atlas.entries
    )
    assert "cross-family refusal surface" in atlas.note
