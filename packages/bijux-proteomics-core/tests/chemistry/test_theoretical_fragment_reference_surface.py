# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.chemistry.theoretical_fragment_reference import (
    TheoreticalFragmentReferenceCase,
    validate_theoretical_fragment_reference_cases,
)


def _chemistry_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "chemistry" / name


def test_validate_theoretical_fragment_reference_cases_matches_curated_fixture() -> (
    None
):
    raw_cases = json.loads(
        _chemistry_fixture("theoretical_fragment_reference_cases.json").read_text()
    )
    cases = [
        TheoreticalFragmentReferenceCase.model_validate(case) for case in raw_cases
    ]

    report = validate_theoretical_fragment_reference_cases(cases)

    assert report.valid is True
    assert report.case_count == 4
    assert report.entry_count == 17
    assert report.failed_entry_count == 0
