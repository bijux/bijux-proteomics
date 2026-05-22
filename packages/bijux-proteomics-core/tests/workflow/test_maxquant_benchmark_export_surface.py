# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_maxquant_benchmark_report,
    render_maxquant_benchmark_summary_tsv,
    render_maxquant_differential_comparison_tsv,
    render_maxquant_filtering_comparison_tsv,
    render_maxquant_lfq_comparison_tsv,
    render_maxquant_protein_identity_comparison_tsv,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_maxquant_benchmark_renderers_emit_stable_ledgers() -> None:
    design_entries = tuple(
        parse_experimental_design_table(_bundle_fixture("design.tsv")).accepted_entries
    )
    report = build_maxquant_benchmark_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
        design_entries=design_entries,
        condition_a="control",
        condition_b="treatment",
    )

    summary_tsv = render_maxquant_benchmark_summary_tsv(report)
    protein_tsv = render_maxquant_protein_identity_comparison_tsv(report)
    filtering_tsv = render_maxquant_filtering_comparison_tsv(report)
    lfq_tsv = render_maxquant_lfq_comparison_tsv(report)
    differential_tsv = render_maxquant_differential_comparison_tsv(report)

    assert "field\tvalue" in summary_tsv
    assert "lfq_values_matched\ttrue" in summary_tsv
    assert "differential_matched\ttrue" in summary_tsv
    assert "source_entity_ids\timported_entity_ids" in protein_tsv
    assert "P04637" in protein_tsv
    assert "entity_id\tsource_disposition\timported_disposition" in filtering_tsv
    assert "CON__KRT1\tfiltered\tfiltered" in filtering_tsv
    assert "entity_id\tsample_id\tsource_intensity\timported_intensity" in lfq_tsv
    assert "P04637\tT1\t1600\t1600\t0\ttrue" in lfq_tsv
    assert (
        "entity_id\tsource_log2_fold_change\timported_log2_fold_change"
        in differential_tsv
    )
    assert "P04637" in differential_tsv
