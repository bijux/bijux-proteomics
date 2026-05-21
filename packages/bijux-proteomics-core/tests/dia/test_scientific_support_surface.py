# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia.benchmarks import (
    WorkflowScientificSupportTier,
    build_dia_workflow_scientific_support_report,
)


def test_build_dia_workflow_scientific_support_report_separates_tiers() -> None:
    report = build_dia_workflow_scientific_support_report(
        imported_precursor_count=92,
        expected_precursor_count=100,
        sample_resolved_precursor_count=88,
        expected_sample_resolved_precursor_count=100,
        transition_supported_precursor_count=73,
        expected_transition_precursor_count=100,
        protein_group_count=61,
        expected_protein_group_count=100,
        sample_resolved_protein_count=58,
        expected_sample_resolved_protein_count=100,
        ion_mobility_observed_count=54,
        ion_mobility_expected_count=100,
        library_matched_peptide_count=81,
        expected_library_peptide_count=100,
        absent_expected_peptide_count=19,
    )

    tiers = {entry.surface: entry.support_tier for entry in report.entries}

    assert tiers["library_conditioned_import"] is WorkflowScientificSupportTier.PARTIAL
    assert tiers["precursor_matrix_evidence"] is WorkflowScientificSupportTier.PARTIAL
    assert tiers["transition_semantics"] is WorkflowScientificSupportTier.PARTIAL
    assert tiers["protein_level_evidence"] is WorkflowScientificSupportTier.PARTIAL
    assert tiers["biological_interpretation"] is WorkflowScientificSupportTier.REFUSED
    assert report.library_coverage_fraction == 0.81
    assert report.ion_mobility_observed_fraction == 0.54
    assert report.absent_expected_peptide_fraction == 0.19
    assert report.ready_for_biological_interpretation is False
    assert "partial DIA support means" in report.partial_support_definition
