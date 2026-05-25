# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated disease and phenotype resolution entrypoints."""

from __future__ import annotations

from bijux_proteomics_knowledge.disease.terms import (
    DiseaseTermResolutionEntry,
    DiseaseTermResolutionReport,
    DiseaseTermResolutionSummary,
    render_disease_term_resolution_tsv,
    resolve_disease_terms,
)

__all__ = [
    "DiseaseTermResolutionEntry",
    "DiseaseTermResolutionReport",
    "DiseaseTermResolutionSummary",
    "render_disease_term_resolution_tsv",
    "resolve_disease_terms",
]
