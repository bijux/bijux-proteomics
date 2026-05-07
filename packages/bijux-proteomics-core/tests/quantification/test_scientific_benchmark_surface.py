# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
)
from bijux_proteomics.quantification.benchmarks import (
    build_effect_size_stability_benchmark_report,
    build_quant_missingness_robustness_report,
    build_quant_normalization_impact_benchmark_report,
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


def test_quant_missingness_robustness_report_surfaces_sparse_and_technical_patterns() -> None:
    report = build_quant_missingness_robustness_report(
        _records(),
        design_entries=_design(),
    )

    assert report.sparse_biology_candidate_count >= 1
    assert report.technical_failure_count >= 1
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

    assert len(report.entries) == 4
    assert report.unsupported_policies
    supported = [entry for entry in report.entries if entry.supported]
    assert all(entry.top_entity_id is not None for entry in supported)


def test_effect_size_stability_benchmark_report_stays_stable_under_small_perturbation() -> None:
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
