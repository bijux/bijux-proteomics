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
