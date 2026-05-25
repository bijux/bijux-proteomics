# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical belief-review and trust-ranking surfaces."""

from __future__ import annotations

from importlib import import_module

_BELIEF_MODULES = (
    "bijux_proteomics.review.belief.belief_audit",
    "bijux_proteomics.review.belief.biomarker_candidate_ranking",
    "bijux_proteomics.review.belief.contracts",
    "bijux_proteomics.review.belief.evidence_aware_ranking",
    "bijux_proteomics.review.belief.flagship_kernel",
)


def __getattr__(name: str) -> object:
    for module_path in _BELIEF_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
