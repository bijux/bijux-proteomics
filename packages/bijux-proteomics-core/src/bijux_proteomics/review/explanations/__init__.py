# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical scientific explanation and narrative surfaces."""

from __future__ import annotations

from importlib import import_module

_EXPLANATION_MODULES = (
    "bijux_proteomics.review.explanations.volcano_plots",
    "bijux_proteomics.review.explanations.scientific_story",
    "bijux_proteomics.review.explanations.scientific_conflicts",
    "bijux_proteomics.review.explanations.result_explanations",
    "bijux_proteomics.review.explanations.failure_explanations",
    "bijux_proteomics.review.explanations.scientific_failure_atlas",
)


def __getattr__(name: str) -> object:
    for module_path in _EXPLANATION_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
