# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia import (
    compare_library_and_database_search_evidence,
)


def test_compare_library_and_database_search_evidence_reports_preferred_source() -> (
    None
):
    report = compare_library_and_database_search_evidence(
        library_q_values={"PEPTIDEK": 0.01, "ACDMPEP": 0.03},
        database_q_values={"PEPTIDEK": 0.02, "ACDMPEP": 0.01},
    )

    assert report.shared_peptide_count == 2
    assert report.entries[0].preferred_source == "database"
    assert report.entries[1].preferred_source == "library"
