# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import (
    parse_ms1_feature_table_with_provenance,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "quant" / name


def test_parse_ms1_feature_table_with_provenance_reports_units_and_optional_fields() -> (
    None
):
    report = parse_ms1_feature_table_with_provenance(_quant_fixture("ms1_features.tsv"))

    assert report.total_rows > 0
    assert report.accepted_rows > 0
    assert report.units["retention_time_seconds"] == "seconds"
    assert report.observed_charge_rows >= 1
    assert report.observed_mz_rows >= 1
