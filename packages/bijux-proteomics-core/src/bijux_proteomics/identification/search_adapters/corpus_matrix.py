# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Conformance matrix assembly across built-in search-adapter corpora."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.search_adapters.corpus import SearchAdapterCorpusConformanceEntry, SearchAdapterCorpusConformanceMatrix, SearchEngineCorpusReport
from bijux_proteomics.identification.search_adapters.engines.comet import build_comet_output_corpus_report
from bijux_proteomics.identification.search_adapters.engines.diann import build_diann_output_corpus_report
from bijux_proteomics.identification.search_adapters.engines.maxquant import build_maxquant_output_corpus_report
from bijux_proteomics.identification.search_adapters.engines.msfragger import build_msfragger_output_corpus_report
from bijux_proteomics.identification.search_adapters.engines.sage import build_sage_output_corpus_report
from bijux_proteomics.identification.search_adapters.engines.spectronaut import build_spectronaut_output_corpus_report


def _corpus_conformance_entry(
    report: SearchEngineCorpusReport,
) -> SearchAdapterCorpusConformanceEntry:
    unsupported_column_count = sum(
        len(entry.unsupported_columns) for entry in report.entries
    )
    lost_column_count = sum(len(entry.lost_columns) for entry in report.entries)
    return SearchAdapterCorpusConformanceEntry(
        adapter_kind=report.adapter_kind,
        corpus_root=report.corpus_root,
        corpus_passes=report.passes,
        corpus_entry_count=len(report.entries),
        total_accepted_rows=report.total_accepted_rows,
        total_rejected_rows=report.total_rejected_rows,
        unsupported_column_count=unsupported_column_count,
        lost_column_count=lost_column_count,
    )


def build_search_adapter_corpus_conformance_matrix(
    matrix_root: Path,
) -> SearchAdapterCorpusConformanceMatrix:
    """Build conformance summaries across built-in adapter corpora."""
    reports = (
        build_comet_output_corpus_report(matrix_root / "comet"),
        build_msfragger_output_corpus_report(matrix_root / "msfragger"),
        build_sage_output_corpus_report(matrix_root / "sage"),
        build_maxquant_output_corpus_report(matrix_root / "maxquant"),
        build_diann_output_corpus_report(matrix_root / "diann"),
        build_spectronaut_output_corpus_report(matrix_root / "spectronaut"),
    )
    entries = tuple(
        sorted(
            (_corpus_conformance_entry(report) for report in reports),
            key=lambda entry: entry.adapter_kind.value,
        )
    )
    return SearchAdapterCorpusConformanceMatrix(
        matrix_root=str(matrix_root),
        entries=entries,
        passes=all(entry.corpus_passes for entry in entries),
    )
