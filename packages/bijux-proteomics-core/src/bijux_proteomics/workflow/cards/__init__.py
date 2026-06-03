"""Workflow card builders over governed proteomics result surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_CARD_EXPORT_MODULES = (
    "bijux_proteomics.workflow.cards.cross_study_evidence_cards",
    "bijux_proteomics.workflow.cards.pathway_evidence_cards",
    "bijux_proteomics.workflow.cards.protein_evidence_cards",
    "bijux_proteomics.workflow.cards.protein_mechanism_cards",
    "bijux_proteomics.workflow.cards.sample_evidence_cards",
)


def __getattr__(name: str) -> Any:
    for module_path in _CARD_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
