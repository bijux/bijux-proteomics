# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated kinase-substrate resolution entrypoints."""

from __future__ import annotations

from bijux_proteomics_knowledge.kinases.substrates import (
    KinaseSubstrateMatchType,
    KinaseSubstrateResolutionEntry,
    KinaseSubstrateResolutionReport,
    KinaseSubstrateResolutionSummary,
    render_kinase_substrate_resolution_tsv,
    resolve_kinase_substrates,
)

__all__ = [
    "KinaseSubstrateMatchType",
    "KinaseSubstrateResolutionEntry",
    "KinaseSubstrateResolutionReport",
    "KinaseSubstrateResolutionSummary",
    "render_kinase_substrate_resolution_tsv",
    "resolve_kinase_substrates",
]
