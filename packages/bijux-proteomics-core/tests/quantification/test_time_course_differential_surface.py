# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    TimeCourseTestingPolicy,
    build_label_free_intensity_table,
    build_time_course_differential_report,
    export_time_course_differential_tsv,
    render_time_course_differential_tsv,
)


def _design_entries(*, labels: tuple[str, ...]) -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="c0_r1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c0_r1.mzml",
            metadata={"timepoint": labels[0]},
        ),
        ExperimentalDesignEntry(
            sample_id="c0_r2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c0_r2.mzml",
            metadata={"timepoint": labels[0]},
        ),
        ExperimentalDesignEntry(
            sample_id="c1_r1",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="c1_r1.mzml",
            metadata={"timepoint": labels[1]},
        ),
        ExperimentalDesignEntry(
            sample_id="c1_r2",
            condition="control",
            replicate=4,
            fraction=1,
            spectra_file="c1_r2.mzml",
            metadata={"timepoint": labels[1]},
        ),
        ExperimentalDesignEntry(
            sample_id="t0_r1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t0_r1.mzml",
            metadata={"timepoint": labels[0]},
        ),
        ExperimentalDesignEntry(
            sample_id="t0_r2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t0_r2.mzml",
            metadata={"timepoint": labels[0]},
        ),
        ExperimentalDesignEntry(
            sample_id="t1_r1",
            condition="treatment",
            replicate=3,
            fraction=1,
            spectra_file="t1_r1.mzml",
            metadata={"timepoint": labels[1]},
        ),
        ExperimentalDesignEntry(
            sample_id="t1_r2",
            condition="treatment",
            replicate=4,
            fraction=1,
            spectra_file="t1_r2.mzml",
            metadata={"timepoint": labels[1]},
        ),
    )


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="tc001",
            sample_id="c0_r1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc002",
            sample_id="c0_r2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc003",
            sample_id="c1_r1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=130.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc004",
            sample_id="c1_r2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc005",
            sample_id="t0_r1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc006",
            sample_id="t0_r2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc007",
            sample_id="t1_r1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=410.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc008",
            sample_id="t1_r2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=430.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="tc101",
            sample_id="c0_r1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=200.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc102",
            sample_id="c0_r2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=210.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc103",
            sample_id="c1_r1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=240.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc104",
            sample_id="c1_r2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=250.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc105",
            sample_id="t0_r1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=205.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc106",
            sample_id="t0_r2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=215.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc107",
            sample_id="t1_r1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=245.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="tc108",
            sample_id="t1_r2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=255.0,
            protein_refs=("P002",),
        ),
    )


def _protein_table():
    return build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_time_course_differential_infers_numeric_prefixed_order_and_interactions() -> (
    None
):
    report = build_time_course_differential_report(
        _protein_table(),
        _design_entries(labels=("t0", "t1")),
    )

    lookup = {(entry.entity_id, entry.condition): entry for entry in report.entries}

    assert report.ordered_timepoints == ("t0", "t1")
    assert report.reference_condition == "control"
    assert report.timepoint_positions == {"t0": 0.0, "t1": 1.0}
    assert lookup[("P001", "treatment")].slope_per_timepoint > lookup[
        ("P001", "control")
    ].slope_per_timepoint
    assert lookup[("P001", "treatment")].interaction_effect is not None
    assert lookup[("P001", "treatment")].interaction_effect > 0.0
    assert lookup[("P001", "treatment")].interaction_p_value is not None
    assert lookup[("P001", "treatment")].interaction_adjusted_p_value is not None
    assert lookup[("P002", "treatment")].interaction_effect is not None
    assert "numeric labels" in report.note
    assert (
        "interaction_adjusted_p_value" in render_time_course_differential_tsv(report)
    )


def test_time_course_differential_requires_explicit_order_for_unordered_labels() -> None:
    try:
        build_time_course_differential_report(
            _protein_table(),
            _design_entries(labels=("baseline", "endpoint")),
        )
    except ValueError as exc:
        assert "missing_timepoint_order" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected unordered timepoint labels to be rejected")


def test_time_course_differential_accepts_explicit_order_and_exports_tsv(
    tmp_path: Path,
) -> None:
    report = build_time_course_differential_report(
        _protein_table(),
        _design_entries(labels=("baseline", "endpoint")),
        policy=TimeCourseTestingPolicy(
            ordered_timepoints=("baseline", "endpoint"),
        ),
    )
    output_path = tmp_path / "time_course.tsv"
    export_time_course_differential_tsv(report, output_path)

    assert report.ordered_timepoints == ("baseline", "endpoint")
    assert "supplied explicitly" in report.note
    assert output_path.read_text(encoding="utf-8").startswith(
        "entity_id\tcondition\treference_condition"
    )
