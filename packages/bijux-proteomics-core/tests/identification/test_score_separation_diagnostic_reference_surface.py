# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.identification.score_separation_diagnostic import (
    ScoreSeparationWarningTier,
    build_score_separation_diagnostic_report,
)


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_score_separation_reference_cases_prove_overlap_and_warning_tiers() -> None:
    raw_cases = json.loads(
        _identification_fixture("score_separation_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )

    for case in raw_cases:
        records = tuple(PsmRecord.model_validate(record) for record in case["records"])
        report = build_score_separation_diagnostic_report(
            records,
            score_orientation=case["score_orientation"],
            bin_count=case["bin_count"],
            warning_overlap_threshold=case["warning_overlap_threshold"],
            unstable_overlap_threshold=case["unstable_overlap_threshold"],
        )

        assert (
            report.summary.target_dominance_fraction
            == case["expected_target_dominance_fraction"]
        )
        assert report.summary.overlap_metric == case["expected_overlap_metric"]
        assert report.summary.warning_tier is ScoreSeparationWarningTier(
            case["expected_warning_tier"]
        )
        assert report.summary.fdr_unstable is case["expected_fdr_unstable"]
