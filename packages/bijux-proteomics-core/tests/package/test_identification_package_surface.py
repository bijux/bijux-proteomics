# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import identification


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "identification" / name


def test_identification_package_exports_psm_target_decoy_fdr_owner_surface() -> None:
    raw_cases = json.loads(
        _identification_fixture("target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        identification.TargetDecoyReferenceCase.model_validate(case)
        for case in raw_cases
    )

    report = identification.build_psm_target_decoy_fdr_report(
        cases[0].records,
        threshold=cases[0].threshold,
        score_orientation=cases[0].score_orientation,
        tie_handling=cases[0].tie_handling,
    )
    rendered = identification.render_psm_target_decoy_fdr_summary_tsv(report)

    assert hasattr(identification, "build_psm_target_decoy_fdr_report")
    assert hasattr(identification, "render_psm_target_decoy_fdr_tsv")
    assert hasattr(identification, "render_psm_target_decoy_fdr_summary_tsv")
    assert report.summary.total_psm_count == len(cases[0].expected_entries)
    assert report.summary.q_values_monotonic is True
    assert "reproducibility_hash" in rendered


def test_identification_package_exports_peptide_target_decoy_fdr_owner_surface() -> (
    None
):
    raw_cases = json.loads(
        _identification_fixture("peptide_target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_peptide_target_decoy_fdr_report(
        records,
        threshold=case["threshold"],
        score_orientation=case["score_orientation"],
        evidence_policy=case["evidence_policy"],
    )
    rendered = identification.render_peptide_target_decoy_fdr_summary_tsv(report)

    assert hasattr(identification, "build_peptide_target_decoy_fdr_report")
    assert hasattr(identification, "render_peptide_target_decoy_fdr_tsv")
    assert hasattr(identification, "render_peptide_target_decoy_fdr_summary_tsv")
    assert report.summary.total_peptide_count == len(case["expected_entries"])
    assert report.summary.q_values_monotonic is True
    assert "evidence_policy" in rendered


def test_identification_package_exports_protein_target_decoy_fdr_owner_surface() -> (
    None
):
    raw_cases = json.loads(
        _identification_fixture("protein_target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_protein_target_decoy_fdr_report(
        records,
        threshold=case["threshold"],
        score_orientation=case["score_orientation"],
        evidence_policy=case["evidence_policy"],
    )
    rendered = identification.render_protein_target_decoy_fdr_summary_tsv(report)

    assert hasattr(identification, "build_protein_target_decoy_fdr_report")
    assert hasattr(identification, "render_protein_target_decoy_fdr_tsv")
    assert hasattr(identification, "render_protein_target_decoy_fdr_summary_tsv")
    assert report.summary.total_protein_count == len(case["expected_entries"])
    assert report.summary.q_values_monotonic is True
    assert "evidence_policy" in rendered


def test_identification_package_exports_picked_protein_fdr_owner_surface() -> None:
    raw_cases = json.loads(
        _identification_fixture("picked_protein_fdr_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_picked_protein_fdr_report_from_psm_records(
        records,
        threshold=case["threshold"],
        score_orientation=case["score_orientation"],
    )
    rendered = identification.render_picked_protein_pair_tsv(report)

    assert hasattr(identification, "build_picked_protein_fdr_report_from_psm_records")
    assert hasattr(identification, "render_picked_protein_pair_tsv")
    assert report.summary.total_pair_count == len(case["expected_entries"])
    assert report.summary.q_values_monotonic is True
    assert rendered.startswith("pair_id\tbase_accession")


def test_identification_package_exports_protein_grouping_owner_surface() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_grouping_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_protein_grouping_report(records)
    rendered = identification.render_protein_grouping_entries_tsv(report)

    assert hasattr(identification, "build_protein_grouping_report")
    assert hasattr(identification, "render_protein_grouping_entries_tsv")
    assert hasattr(identification, "render_protein_grouping_summary_tsv")
    assert report.summary.total_groups == len(case["expected_groups"])
    assert report.reproducibility_hash
    assert rendered.startswith("group_id\trepresentative_protein")


def test_identification_package_exports_protein_coverage_owner_surface() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_coverage_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_protein_coverage_report(
        records,
        protein_sequences=case["protein_sequences"],
        threshold=case["threshold"],
        score_orientation=case["score_orientation"],
    )
    rendered = identification.render_protein_coverage_summary_tsv(report)

    assert hasattr(identification, "build_protein_coverage_report")
    assert hasattr(identification, "render_protein_coverage_uncovered_regions_tsv")
    assert hasattr(identification, "render_protein_coverage_peptide_coordinates_tsv")
    assert report.summary.total_covered_residues == 6
    assert report.reproducibility_hash
    assert "reproducibility_hash" in rendered


def test_identification_package_exports_peptide_evidence_owner_surface() -> None:
    raw_cases = json.loads(
        _identification_fixture("peptide_evidence_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_peptide_evidence_report(
        records,
        threshold=case["threshold"],
        score_orientation=case["score_orientation"],
        strong_q_value=case["strong_q_value"],
        reproducible_spectrum_count=case["reproducible_spectrum_count"],
    )
    rendered = identification.render_peptide_evidence_summary_tsv(report)

    assert hasattr(identification, "build_peptide_evidence_report")
    assert hasattr(identification, "render_peptide_evidence_entries_tsv")
    assert hasattr(identification, "render_peptide_evidence_summary_tsv")
    assert report.summary.shared_count == 1
    assert report.summary.ambiguous_count == 1
    assert report.reproducibility_hash
    assert "reproducibility_hash" in rendered


def test_identification_package_exports_contaminant_evidence_owner_surface() -> None:
    records = (
        identification.PsmRecord(
            spectrum_id="run-a:scan-001",
            peptide="KERATINP",
            canonical_peptide="KERATINP",
            charge=2,
            score=65.0,
            q_value=0.004,
            intensity=800.0,
            protein_refs=("CON__K1C10_HUMAN",),
            target_decoy_label=identification.TargetDecoyLabel.TARGET,
            run_id="run-a",
        ),
        identification.PsmRecord(
            spectrum_id="run-a:scan-002",
            peptide="TARGETP",
            canonical_peptide="TARGETP",
            charge=2,
            score=58.0,
            q_value=0.010,
            intensity=1000.0,
            protein_refs=("P12345",),
            target_decoy_label=identification.TargetDecoyLabel.TARGET,
            run_id="run-a",
        ),
    )

    report = identification.build_contaminant_evidence_report(
        records,
        sample_id_by_run={"run-a": "sample-a"},
        warning_psm_fraction=0.4,
        warning_intensity_fraction=0.4,
    )
    rendered = identification.render_contaminant_burden_tsv(report)

    assert hasattr(identification, "build_contaminant_evidence_report")
    assert hasattr(identification, "render_contaminant_burden_tsv")
    assert hasattr(identification, "render_contaminant_proteins_tsv")
    assert report.summary.contaminant_psm_count == 1
    assert report.summary.burdened_run_count == 1
    assert report.reproducibility_hash
    assert "heavy_contaminant_warning" in rendered


def test_identification_package_exports_protein_parsimony_owner_surface() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_parsimony_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = raw_cases[0]
    records = tuple(
        identification.PsmRecord.model_validate(record) for record in case["records"]
    )

    report = identification.build_protein_parsimony_report(
        records,
        variant=identification.ParsimonyVariant(case["variant"]),
        review_variants=tuple(
            identification.ParsimonyVariant(value)
            for value in case["review_variants"]
        ),
    )
    rendered = identification.render_protein_parsimony_summary_tsv(report)

    assert hasattr(identification, "build_protein_parsimony_report")
    assert hasattr(identification, "render_protein_parsimony_summary_tsv")
    assert hasattr(identification, "render_protein_parsimony_proteins_tsv")
    assert hasattr(identification, "render_protein_parsimony_ambiguities_tsv")
    assert report.summary.selected_protein_count == len(
        case["expected_selected_proteins"]
    )
    assert report.reproducibility_hash
    assert "reproducibility_hash" in rendered
