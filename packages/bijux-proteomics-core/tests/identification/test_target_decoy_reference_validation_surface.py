# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification import (
    TargetDecoyReferenceCase,
    build_target_decoy_reference_validation_report,
    render_target_decoy_reference_entries_tsv,
    render_target_decoy_reference_summary_tsv,
)
from bijux_proteomics.identification.psm_target_decoy_fdr import (
    build_psm_target_decoy_fdr_report,
)


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_target_decoy_reference_validation_matches_curated_cases() -> None:
    raw_cases = json.loads(
        _identification_fixture("target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(TargetDecoyReferenceCase.model_validate(case) for case in raw_cases)

    report = build_target_decoy_reference_validation_report(cases)

    assert report.valid is True
    assert report.case_count == 2
    assert report.entry_count == 10
    assert report.failed_entry_count == 0
    assert {case.score_orientation for case in report.cases} == {
        "higher_better",
        "lower_better",
    }
    higher = next(
        case
        for case in report.cases
        if case.case_id == "concatenated_higher_better_reference"
    )
    assert higher.q_values_monotonic is True
    assert higher.entries[1].observed_q_value == 0.5
    assert higher.entries[-1].observed_cumulative_targets == 3
    lower = next(
        case
        for case in report.cases
        if case.case_id == "concatenated_lower_better_reference"
    )
    assert lower.entries[0].observed_fdr == 0.0
    assert lower.entries[3].observed_accepted is False
    direct_engine = build_psm_target_decoy_fdr_report(
        cases[0].records,
        threshold=cases[0].threshold,
        score_orientation=cases[0].score_orientation,
        tie_handling=cases[0].tie_handling,
    )
    assert higher.reproducibility_hash == direct_engine.reproducibility_hash


def test_target_decoy_reference_validation_renders_summary_and_entry_ledgers() -> None:
    raw_cases = json.loads(
        _identification_fixture("target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(TargetDecoyReferenceCase.model_validate(case) for case in raw_cases)

    report = build_target_decoy_reference_validation_report(cases)
    summary_tsv = render_target_decoy_reference_summary_tsv(report)
    entries_tsv = render_target_decoy_reference_entries_tsv(report)

    assert summary_tsv.startswith(
        "case_id\tscore_orientation\ttie_handling\tthreshold\tvalid"
    )
    assert "concatenated_higher_better_reference" in summary_tsv
    assert "concatenated_lower_better_reference\tlower_better" in summary_tsv
    assert entries_tsv.startswith(
        "case_id\trank\tspectrum_id\tcanonical_peptide\tpassed"
    )
    assert (
        "concatenated_higher_better_reference\t2\tscan=4002\tDECOYPEP\ttrue"
        in entries_tsv
    )
    assert (
        "concatenated_lower_better_reference\t5\tscan=5005\tPEPK\ttrue" in entries_tsv
    )
