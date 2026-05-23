# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.quantification as quantification
from bijux_proteomics.io.formats import ExperimentalDesignEntry


def test_quantification_package_exports_time_course_differential_owner_surface() -> (
    None
):
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="pkg001",
            sample_id="c0",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg002",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg003",
            sample_id="t0",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg004",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=420.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg005",
            sample_id="c0",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=200.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg006",
            sample_id="c1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=240.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg007",
            sample_id="t0",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=205.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg008",
            sample_id="t1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=245.0,
            protein_refs=("P002",),
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="c0",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c0.mzml",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c1.mzml",
            metadata={"timepoint": "1"},
        ),
        ExperimentalDesignEntry(
            sample_id="t0",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t0.mzml",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t1.mzml",
            metadata={"timepoint": "1"},
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.build_time_course_differential_report(
        table,
        design_entries,
    )
    rendered = quantification.render_time_course_differential_tsv(report)

    assert hasattr(quantification, "build_time_course_differential_report")
    assert hasattr(quantification, "render_time_course_differential_tsv")
    assert hasattr(quantification, "export_time_course_differential_tsv")
    assert report.ordered_timepoints == ("0", "1")
    assert len(report.entries) == 4
    assert rendered.startswith("entity_id\tcondition\treference_condition")
