# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    MultiConditionDifferentialAbundanceReport,
    MultiContrastMagnitudeConsistencyStatus,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_multi_condition_differential_abundance_report,
    build_multi_contrast_consistency_report,
    render_multi_contrast_consistency_tsv,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-1",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="rescue-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-2",
            condition="rescue",
            replicate=2,
            fraction=1,
            spectra_file="rescue-2.mzml",
        ),
    )


def _report() -> MultiConditionDifferentialAbundanceReport:
    records = (
        Ms1FeatureRecord(
            feature_id="mc-001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-002",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=125.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-003",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=600.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=610.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-005",
            sample_id="rescue-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=300.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-006",
            sample_id="rescue-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=290.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=800.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-008",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=780.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-009",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=200.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-010",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=210.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-011",
            sample_id="rescue-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=500.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-012",
            sample_id="rescue-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=490.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-013",
            sample_id="ctrl-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=90.0,
            protein_refs=("P003",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-014",
            sample_id="ctrl-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=95.0,
            protein_refs=("P003",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-015",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=100.0,
            protein_refs=("P003",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-016",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=105.0,
            protein_refs=("P003",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-017",
            sample_id="rescue-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=94.0,
            protein_refs=("P003",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-018",
            sample_id="rescue-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=93.0,
            protein_refs=("P003",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return build_multi_condition_differential_abundance_report(table, _design())


def test_multi_contrast_consistency_flags_shared_hits_and_magnitude_status() -> None:
    base_report = _report()
    adjusted_reports = []
    for contrast_report in base_report.reports:
        adjusted_entries = []
        for entry in contrast_report.entries:
            if entry.entity_id != "P003":
                adjusted_entries.append(entry)
                continue
            if (
                contrast_report.condition_a,
                contrast_report.condition_b,
            ) == ("case", "control"):
                adjusted_entries.append(
                    entry.model_copy(
                        update={
                            "log2_fold_change": 0.9,
                            "adjusted_p_value": 0.01,
                        }
                    )
                )
            else:
                adjusted_entries.append(
                    entry.model_copy(
                        update={
                            "log2_fold_change": 0.05,
                            "adjusted_p_value": 0.5,
                        }
                    )
                )
        adjusted_reports.append(
            contrast_report.model_copy(update={"entries": tuple(adjusted_entries)})
        )
    report = build_multi_contrast_consistency_report(
        base_report.model_copy(update={"reports": tuple(adjusted_reports)}),
        entity_protein_refs={
            "P001": ("P001",),
            "P002": ("P002",),
            "P003": ("P003",),
        },
    )

    by_entity = {entry.entity_id: entry for entry in report.entities}

    assert report.summary.entity_count == 3
    assert report.summary.shared_hit_count == 2
    assert report.summary.contrast_specific_hit_count == 1
    assert by_entity["P001"].shared_hit is True
    assert by_entity["P001"].direction_conflict is False
    assert (
        by_entity["P001"].magnitude_consistency_status
        is MultiContrastMagnitudeConsistencyStatus.VARIABLE
    )
    assert by_entity["P003"].contrast_specific_hit is True
    assert by_entity["P003"].contrast_specific_contrast_labels == ("case_vs_control",)
    assert "direction_conflict" in render_multi_contrast_consistency_tsv(report)


def test_multi_contrast_consistency_flags_direction_cycles() -> None:
    report = _report()
    conflict_entity = "P001"
    updated_reports = []
    for contrast_report in report.reports:
        updated_entries = []
        for entry in contrast_report.entries:
            if entry.entity_id != conflict_entity:
                updated_entries.append(entry)
                continue
            log2_fold_change = entry.log2_fold_change
            if (
                contrast_report.condition_a,
                contrast_report.condition_b,
            ) == ("case", "control"):
                log2_fold_change = 2.0
            elif (
                contrast_report.condition_a,
                contrast_report.condition_b,
            ) == ("case", "rescue"):
                log2_fold_change = -1.2
            elif (
                contrast_report.condition_a,
                contrast_report.condition_b,
            ) == ("control", "rescue"):
                log2_fold_change = 1.1
            updated_entries.append(
                entry.model_copy(
                    update={
                        "log2_fold_change": log2_fold_change,
                        "adjusted_p_value": 0.001,
                    }
                )
            )
        updated_reports.append(
            contrast_report.model_copy(update={"entries": tuple(updated_entries)})
        )
    conflict_report = report.model_copy(update={"reports": tuple(updated_reports)})

    consistency = build_multi_contrast_consistency_report(conflict_report)
    conflict_entry = next(
        entry for entry in consistency.entities if entry.entity_id == conflict_entity
    )

    assert consistency.summary.direction_conflict_count == 1
    assert conflict_entry.direction_conflict is True
    assert conflict_entry.direction_relations == (
        "case>control",
        "rescue>case",
        "control>rescue",
    )
