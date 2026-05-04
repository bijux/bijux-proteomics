# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia import (
    DiaIonMobilityEvidenceEntry,
    build_dia_ion_mobility_evidence_report,
)


def test_build_dia_ion_mobility_evidence_report_counts_used_entries() -> None:
    report = build_dia_ion_mobility_evidence_report(
        (
            DiaIonMobilityEvidenceEntry(
                precursor_id="p1",
                run_id="run-1",
                ion_mobility_ms_per_cm2=1.2,
                ccs_angstrom2=220.3,
                evidence_used=True,
                note="mobility filter improved selectivity",
            ),
            DiaIonMobilityEvidenceEntry(
                precursor_id="p2",
                run_id="run-1",
                ion_mobility_ms_per_cm2=1.4,
                ccs_angstrom2=240.8,
                evidence_used=False,
                note="mobility captured but not used by method",
            ),
        )
    )

    assert report.used_count == 1
    assert report.entries[0].precursor_id == "p1"
