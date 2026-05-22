# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_maxquant_benchmark_report


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_build_maxquant_benchmark_report_preserves_accepted_protein_group_identity() -> (
    None
):
    report = build_maxquant_benchmark_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
    )

    assert report.summary.source_protein_group_count == 8
    assert report.summary.imported_protein_group_count == 8
    assert report.summary.source_accepted_protein_group_count == 5
    assert report.summary.imported_accepted_protein_group_count == 5
    assert report.summary.source_filtered_protein_group_count == 3
    assert report.summary.imported_filtered_protein_group_count == 3
    assert report.summary.protein_identity_matched is True
    assert report.protein_identity_comparison.missing_in_import == ()
    assert report.protein_identity_comparison.extra_in_import == ()
    assert report.protein_identity_comparison.source_entity_ids == (
        "O14920",
        "P04637",
        "P62993",
        "Q8N158",
        "Q9Y243",
    )


def test_build_maxquant_benchmark_report_preserves_filtering_reasons() -> None:
    report = build_maxquant_benchmark_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
    )

    filtering_by_entity = {
        entry.entity_id: entry for entry in report.filtering_comparisons
    }

    assert report.summary.filtering_matched is True
    assert filtering_by_entity["CON__KRT1"].source_reasons == (
        filtering_by_entity["CON__KRT1"].imported_reasons
    )
    assert filtering_by_entity["REV__P77777"].source_reasons == (
        filtering_by_entity["REV__P77777"].imported_reasons
    )
    assert filtering_by_entity["P12345"].source_reasons == (
        filtering_by_entity["P12345"].imported_reasons
    )
    assert filtering_by_entity["CON__KRT1"].source_disposition.value == "filtered"
    assert filtering_by_entity["P04637"].source_disposition.value == "accepted"
