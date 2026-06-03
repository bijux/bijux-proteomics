# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical review-card and handoff surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_CARD_MODULES = (
    "bijux_proteomics.review.cards.queryable_cards",
    "bijux_proteomics.review.cards.collaboration",
    "bijux_proteomics.review.cards.compact_result_summary",
    "bijux_proteomics.review.cards.inference_packets",
    "bijux_proteomics.review.cards.protein_family_graphs",
)


def __getattr__(name: str) -> Any:
    for module_path in _CARD_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
