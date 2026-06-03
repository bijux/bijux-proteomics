# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated knowledge coverage entrypoints."""

from __future__ import annotations

from bijux_proteomics_knowledge.coverage.report import (
    KnowledgeCoverageEntitySet,
    KnowledgeCoverageEntityType,
    KnowledgeCoverageEntry,
    KnowledgeCoveragePolicy,
    KnowledgeCoverageReport,
    KnowledgeCoverageSummary,
    compute_knowledge_coverage,
    render_knowledge_coverage_tsv,
)

__all__ = [
    "KnowledgeCoverageEntitySet",
    "KnowledgeCoverageEntityType",
    "KnowledgeCoverageEntry",
    "KnowledgeCoveragePolicy",
    "KnowledgeCoverageReport",
    "KnowledgeCoverageSummary",
    "compute_knowledge_coverage",
    "render_knowledge_coverage_tsv",
]
