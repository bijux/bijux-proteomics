# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical claim-review surfaces."""

from __future__ import annotations

from importlib import import_module

_CLAIM_MODULES = (
    "bijux_proteomics.review.claims.analysis_recommendations",
    "bijux_proteomics.review.claims.biological_claim_validation",
    "bijux_proteomics.review.claims.biological_hypotheses",
    "bijux_proteomics.review.claims.result_queries",
)


def __getattr__(name: str) -> object:
    for module_path in _CLAIM_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
