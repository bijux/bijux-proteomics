# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Curated package-root interface examples for Bijux Proteomics Core."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics.interfaces.examples import (
        CoreScientificExample,
        ScientificExampleObservation,
        build_glycopeptide_refusal_example,
        build_loss_aware_search_normalization_example,
        build_sequence_digest_example,
    )

__all__ = (
    "CoreScientificExample",
    "ScientificExampleObservation",
    "build_glycopeptide_refusal_example",
    "build_loss_aware_search_normalization_example",
    "build_sequence_digest_example",
)

_ROOT_EXPORTS = {
    "CoreScientificExample": (
        "bijux_proteomics.interfaces.examples",
        "CoreScientificExample",
    ),
    "ScientificExampleObservation": (
        "bijux_proteomics.interfaces.examples",
        "ScientificExampleObservation",
    ),
    "build_glycopeptide_refusal_example": (
        "bijux_proteomics.interfaces.examples",
        "build_glycopeptide_refusal_example",
    ),
    "build_loss_aware_search_normalization_example": (
        "bijux_proteomics.interfaces.examples",
        "build_loss_aware_search_normalization_example",
    ),
    "build_sequence_digest_example": (
        "bijux_proteomics.interfaces.examples",
        "build_sequence_digest_example",
    ),
}


def __getattr__(name: str) -> Any:
    """Load curated interface examples lazily so package imports stay lightweight."""

    target = _ROOT_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
