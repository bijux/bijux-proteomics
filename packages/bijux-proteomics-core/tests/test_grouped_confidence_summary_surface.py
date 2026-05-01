# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification_iteration04 import (
    GroupedConfidenceCategory,
    build_grouped_confidence_summary_report,
)


def _records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="grp-001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=100.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="grp-002",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=95.0,
            q_value=0.002,
            protein_refs=("P22222", "P33333"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="grp-003",
            peptide="PEPC",
            canonical_peptide="PEPC",
            charge=2,
            score=90.0,
            q_value=0.005,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_grouped_confidence_summary_report_separates_categories() -> None:
    report = build_grouped_confidence_summary_report(_records())

    by_category = {entry.category: entry for entry in report.entries}
    assert set(by_category) == {
        GroupedConfidenceCategory.SINGLE_PROTEIN,
        GroupedConfidenceCategory.PROTEIN_GROUP,
        GroupedConfidenceCategory.PROTEIN_FAMILY,
    }
    assert by_category[GroupedConfidenceCategory.SINGLE_PROTEIN].group_count >= 1
    assert (
        by_category[GroupedConfidenceCategory.PROTEIN_GROUP].group_count
        + by_category[GroupedConfidenceCategory.PROTEIN_FAMILY].group_count
        >= 1
    )
