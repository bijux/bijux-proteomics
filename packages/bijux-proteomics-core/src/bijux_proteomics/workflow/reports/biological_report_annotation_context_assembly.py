# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Annotation-context assembly for biological report bundles."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation.biological_context_mapping import (
    build_biological_context_mapping_report,
    parse_biological_context_table,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.biological_context_mapping import (
        BiologicalContextImportReport,
        BiologicalContextMappingReport,
    )
    from bijux_proteomics.interpretation.protein_annotation_mapping import (
        ProteinReferenceEntry,
    )


class BiologicalAnnotationContextReports(NamedTuple):
    """Annotation-context outputs owned by biological context assembly."""

    context_import_report: BiologicalContextImportReport | None
    context_mapping_report: BiologicalContextMappingReport | None


def _build_biological_annotation_context_reports(
    *,
    differential_reference_entries: tuple[ProteinReferenceEntry, ...],
    context_annotation_tsv_path: Path | None,
) -> BiologicalAnnotationContextReports:
    if context_annotation_tsv_path is None:
        return BiologicalAnnotationContextReports(
            context_import_report=None,
            context_mapping_report=None,
        )

    context_import_report = parse_biological_context_table(context_annotation_tsv_path)
    context_mapping_report = build_biological_context_mapping_report(
        differential_reference_entries,
        context_import_report.accepted_records,
    )
    return BiologicalAnnotationContextReports(
        context_import_report=context_import_report,
        context_mapping_report=context_mapping_report,
    )
