# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical evidence-graph review surfaces."""

from __future__ import annotations

from importlib import import_module

_EVIDENCE_GRAPH_MODULES = (
    "bijux_proteomics.review.evidence_graph.evidence_graph",
    "bijux_proteomics.review.evidence_graph.evidence_graph_confidence",
    "bijux_proteomics.review.evidence_graph.evidence_graph_contradictions",
    "bijux_proteomics.review.evidence_graph.evidence_graph_downgrades",
    "bijux_proteomics.review.evidence_graph.evidence_graph_export",
    "bijux_proteomics.review.evidence_graph.evidence_graph_queries",
    "bijux_proteomics.review.evidence_graph.evidence_graph_run_diff",
    "bijux_proteomics.review.evidence_graph.evidence_chain_reconstruction",
)


def __getattr__(name: str) -> object:
    for module_path in _EVIDENCE_GRAPH_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
