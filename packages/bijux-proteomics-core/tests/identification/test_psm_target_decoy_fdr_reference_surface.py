# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification.psm_target_decoy_fdr import (
    build_psm_target_decoy_fdr_report,
)
from bijux_proteomics.identification.target_decoy_reference_validation import (
    TargetDecoyReferenceCase,
)


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_psm_target_decoy_fdr_engine_matches_curated_reference_cases() -> None:
    raw_cases = json.loads(
        _identification_fixture("target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(TargetDecoyReferenceCase.model_validate(case) for case in raw_cases)

    assert {case.score_orientation for case in cases} == {
        "higher_better",
        "lower_better",
    }
    for case in cases:
        report = build_psm_target_decoy_fdr_report(
            case.records,
            threshold=case.threshold,
            score_orientation=case.score_orientation,
            tie_handling=case.tie_handling,
        )

        assert report.summary.q_values_monotonic is True
        assert len(report.entries) == len(case.expected_entries)
        for observed, expected in zip(
            report.entries, case.expected_entries, strict=True
        ):
            assert observed.rank == expected.rank
            assert observed.psm.spectrum_id == expected.spectrum_id
            assert observed.psm.canonical_peptide == expected.canonical_peptide
            assert observed.cumulative_targets == expected.cumulative_targets
            assert observed.cumulative_decoys == expected.cumulative_decoys
            assert observed.raw_fdr == expected.fdr
            assert observed.q_value == expected.q_value
            assert observed.accepted is expected.accepted


def test_psm_target_decoy_fdr_engine_is_reproducible_for_reference_payloads() -> None:
    raw_cases = json.loads(
        _identification_fixture("target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = TargetDecoyReferenceCase.model_validate(raw_cases[0])

    first = build_psm_target_decoy_fdr_report(
        case.records,
        threshold=case.threshold,
        score_orientation=case.score_orientation,
        tie_handling=case.tie_handling,
    )
    second = build_psm_target_decoy_fdr_report(
        case.records,
        threshold=case.threshold,
        score_orientation=case.score_orientation,
        tie_handling=case.tie_handling,
    )

    assert first.reproducibility_hash == second.reproducibility_hash
