# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated protein feature overlap entrypoints."""

from __future__ import annotations

from bijux_proteomics_knowledge.features.overlaps import (
    ProteinFeatureOverlapEntry,
    ProteinFeatureQueryInterval,
    ProteinFeatureType,
    overlap_protein_features,
    render_protein_feature_overlaps_tsv,
)

__all__ = [
    "ProteinFeatureOverlapEntry",
    "ProteinFeatureQueryInterval",
    "ProteinFeatureType",
    "overlap_protein_features",
    "render_protein_feature_overlaps_tsv",
]
