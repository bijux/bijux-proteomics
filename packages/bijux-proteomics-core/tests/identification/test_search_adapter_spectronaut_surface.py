# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.search_adapters import (
    SearchAdapterKind,
    build_spectronaut_output_corpus_report,
)


def _corpus_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_adapter_corpora"
        / "spectronaut"
    )


def test_spectronaut_output_corpus_report_covers_native_and_pipeline_exports() -> None:
    report = build_spectronaut_output_corpus_report(_corpus_root())

    assert report.adapter_kind is SearchAdapterKind.SPECTRONAUT
    assert report.missing_artifacts == ()
    assert report.total_accepted_rows == 6
    assert report.total_rejected_rows == 0
    assert report.passes is True
    assert {entry.dialect_id for entry in report.entries} == {
        "default",
        "pipeline-export",
    }
    for entry in report.entries:
        assert entry.source_sha256
        assert entry.config_sha256
        assert any(
            column in entry.mapped_columns for column in ("EG.Cscore", "cscore_value")
        )
        assert entry.unsupported_columns == ()
