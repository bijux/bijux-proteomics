# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.identification.error_rate_annotation import (
    build_psm_error_rate_annotation_report,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_error_rate_annotation_reference_cases_preserve_imported_vs_computed_semantics() -> (
    None
):
    raw_cases = json.loads(
        _fixture("error_rate_annotation_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )

    for case in raw_cases:
        records = tuple(PsmRecord.model_validate(record) for record in case["records"])
        report = build_psm_error_rate_annotation_report(
            records,
            score_orientation=case["score_orientation"],
            local_window_size=case["local_window_size"],
        )
        expected_entries = {
            entry["spectrum_id"]: entry for entry in case["expected_entries"]
        }

        assert (
            report.summary.imported_pep_count
            == case["expected_summary"]["imported_pep_count"]
        )
        assert (
            report.summary.computed_local_fdr_count
            == case["expected_summary"]["computed_local_fdr_count"]
        )
        assert (
            report.summary.unavailable_count
            == case["expected_summary"]["unavailable_count"]
        )
        for entry in report.entries:
            expected = expected_entries[entry.psm.spectrum_id]
            assert entry.imported_pep == expected["imported_pep"]
            assert entry.computed_local_fdr == expected["computed_local_fdr"]
            assert entry.provenance_flag.value == expected["provenance_flag"]
