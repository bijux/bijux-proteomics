# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    MissingChannelPolicy,
    MissingValueKind,
    Ms1FeatureRecord,
    MultiplexNormalizationPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.benchmarks import (
    MultiplexRatioExpectation,
    QuantTruthDirection,
    QuantTruthExpectationEntry,
    build_effect_size_stability_benchmark_report,
    build_multiplex_artifact_pressure_benchmark_report,
    build_multiplex_stress_benchmark_report,
    build_quant_missingness_robustness_report,
    build_quant_normalization_impact_benchmark_report,
    build_quant_truth_package_benchmark_report,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
            batch="b2",
        ),
    )


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="mnar-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=950.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=990.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-005",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=700.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-006",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=715.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=705.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-008",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-009",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=120.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-010",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=130.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-011",
            sample_id="ctrl-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=1100.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mnar-012",
            sample_id="ctrl-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=1080.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def test_quant_missingness_robustness_report_surfaces_sparse_and_technical_patterns() -> (
    None
):
    report = build_quant_missingness_robustness_report(
        _records(),
        design_entries=_design(),
    )

    assert report.sparse_biology_candidate_count >= 1
    assert report.technical_failure_count >= 1
    assert report.missingness_entity_summary.entries
    assert report.missingness_condition_summary.entries
    assert report.missingness_intensity_dependence.plot_points
    assert report.decision_readiness.readiness_state.value in {
        "decision_grade",
        "review_grade",
        "blocked",
    }


def test_quant_normalization_impact_benchmark_report_tracks_policy_drift() -> None:
    report = build_quant_normalization_impact_benchmark_report(
        _records(),
        design_entries=_design(),
        condition_a="case",
        condition_b="ctrl",
    )

    assert len(report.entries) == 5
    assert report.unsupported_policies == ()
    supported = [entry for entry in report.entries if entry.supported]
    assert all(entry.top_entity_id is not None for entry in supported)


def test_effect_size_stability_benchmark_report_stays_stable_under_small_perturbation() -> (
    None
):
    baseline = _records()
    perturbed = tuple(
        record.model_copy(
            update={
                "intensity": (
                    round(record.intensity * 1.02, 3)
                    if record.intensity is not None and record.sample_id.endswith("1")
                    else record.intensity
                )
            }
        )
        for record in baseline
    )
    report = build_effect_size_stability_benchmark_report(
        baseline,
        perturbed,
        design_entries=_design(),
        condition_a="case",
        condition_b="ctrl",
    )

    assert report.stable_top_rank is True
    assert report.overlap_fraction >= 0.5


def _multiplex_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="plex-a-126",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="plex-a-126.mzml",
            batch="plex-a",
            multiplex_group="plex-a",
            multiplex_channel="126",
        ),
        ExperimentalDesignEntry(
            sample_id="plex-a-127",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="plex-a-127.mzml",
            batch="plex-a",
            multiplex_group="plex-a",
            multiplex_channel="127",
        ),
    )


def _multiplex_records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="plex-001",
            sample_id="plex-a-126",
            peptide="SPIKEA",
            canonical_peptide="SPIKEA",
            intensity=200.0,
            protein_refs=("SPIKEA",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="plex-002",
            sample_id="plex-a-127",
            peptide="SPIKEA",
            canonical_peptide="SPIKEA",
            intensity=100.0,
            protein_refs=("SPIKEA",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="plex-003",
            sample_id="plex-a-126",
            peptide="SPIKEB",
            canonical_peptide="SPIKEB",
            intensity=220.0,
            protein_refs=("SPIKEB",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="plex-004",
            sample_id="plex-a-127",
            peptide="SPIKEB",
            canonical_peptide="SPIKEB",
            intensity=140.0,
            protein_refs=("SPIKEB",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _truth_records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="truth-001",
            sample_id="case-1",
            peptide="TRUTHA",
            canonical_peptide="TRUTHA",
            intensity=1200.0,
            protein_refs=("TP1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-002",
            sample_id="case-2",
            peptide="TRUTHA",
            canonical_peptide="TRUTHA",
            intensity=1180.0,
            protein_refs=("TP1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-003",
            sample_id="ctrl-1",
            peptide="TRUTHA",
            canonical_peptide="TRUTHA",
            intensity=120.0,
            protein_refs=("TP1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-004",
            sample_id="ctrl-2",
            peptide="TRUTHA",
            canonical_peptide="TRUTHA",
            intensity=130.0,
            protein_refs=("TP1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-005",
            sample_id="case-1",
            peptide="TRUTHB",
            canonical_peptide="TRUTHB",
            intensity=110.0,
            protein_refs=("TP2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-006",
            sample_id="case-2",
            peptide="TRUTHB",
            canonical_peptide="TRUTHB",
            intensity=115.0,
            protein_refs=("TP2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-007",
            sample_id="ctrl-1",
            peptide="TRUTHB",
            canonical_peptide="TRUTHB",
            intensity=900.0,
            protein_refs=("TP2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="truth-008",
            sample_id="ctrl-2",
            peptide="TRUTHB",
            canonical_peptide="TRUTHB",
            intensity=920.0,
            protein_refs=("TP2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def test_multiplex_artifact_pressure_benchmark_report_surfaces_compression_and_bleed() -> (
    None
):
    table = build_label_free_intensity_table(
        _multiplex_records(),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_multiplex_artifact_pressure_benchmark_report(
        table,
        design_entries=_multiplex_design(),
        expected_ratios=(
            MultiplexRatioExpectation(
                numerator_sample_id="plex-a-126",
                denominator_sample_id="plex-a-127",
                expected_ratio=4.0,
            ),
        ),
        interference_fraction_by_sample={"plex-a-126": 0.12},
        reporter_bleed_fraction_by_sample={"plex-a-127": 0.18},
    )

    assert report.materially_compressed_count == 1
    assert report.interference_flagged_channel_count == 1
    assert report.reporter_bleed_flagged_channel_count == 1
    assert report.ready_for_ratio_claims is False


def test_quant_truth_package_benchmark_report_tracks_controlled_shifts() -> None:
    report = build_quant_truth_package_benchmark_report(
        _truth_records(),
        design_entries=_design(),
        expectations=(
            QuantTruthExpectationEntry(
                entity_id="TP1",
                expected_direction=QuantTruthDirection.UP_IN_CONDITION_A,
                minimum_absolute_log2_fold_change=1.0,
            ),
            QuantTruthExpectationEntry(
                entity_id="TP2",
                expected_direction=QuantTruthDirection.UP_IN_CONDITION_B,
                minimum_absolute_log2_fold_change=1.0,
            ),
        ),
        condition_a="case",
        condition_b="ctrl",
    )

    assert report.matched_expected_count == 2
    assert report.missed_expected_count == 0
    assert report.unexpected_leader_ids == ()


def test_multiplex_stress_benchmark_report_flags_reference_dropout_and_unbalanced_design() -> (
    None
):
    design_entries = _multiplex_design() + (
        ExperimentalDesignEntry(
            sample_id="plex-a-128",
            condition="carrier",
            replicate=1,
            fraction=1,
            spectra_file="plex-a-128.mzml",
            batch="plex-a",
            multiplex_group="plex-a",
            multiplex_channel="128",
        ),
    )
    records = _multiplex_records() + (
        Ms1FeatureRecord(
            feature_id="plex-005",
            sample_id="plex-a-128",
            peptide="SPIKEC",
            canonical_peptide="SPIKEC",
            intensity=900.0,
            protein_refs=("SPIKEC",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    policy = LabelBasedQuantPolicy(
        missing_channel_policy=MissingChannelPolicy.PRESERVE,
        channel_entries=(
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="127",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="128",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="129",
                channel_role=LabelBasedChannelRole.REFERENCE,
            ),
        ),
    )

    report = build_multiplex_stress_benchmark_report(
        table,
        design_entries=design_entries,
        policy=policy,
        normalization_policy=MultiplexNormalizationPolicy(balance_ratio_threshold=1.2),
    )

    assert report.reference_dropout_count == 1
    assert report.bundle_missing_channel_count >= 1
    assert report.ready_for_biological_rollup is False
