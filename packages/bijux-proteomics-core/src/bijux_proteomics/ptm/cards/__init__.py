# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical PTM review-card, report, and benchmark owners."""

from __future__ import annotations

from importlib import import_module

_CARDS_EXPORT_MODULES = (
    "bijux_proteomics.ptm.cards.benchmarks",
    "bijux_proteomics.ptm.cards.evidence_cards",
    "bijux_proteomics.ptm.cards.proteoforms",
    "bijux_proteomics.ptm.cards.reporting",
    "bijux_proteomics.ptm.cards.review",
)


def __getattr__(name: str) -> object:
    for module_path in _CARDS_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
