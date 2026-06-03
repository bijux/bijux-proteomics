# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated public entrypoints for the core proteomics package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics.identification import build_fdr_audit_trail
    from bijux_proteomics.io.formats import (
        build_normalized_run_bundle,
        parse_experimental_design_table,
    )
    from bijux_proteomics.sequences import parse_fasta_document
    from bijux_proteomics.sequences.digestion import DigestPolicy

__all__ = (
    "DigestPolicy",
    "parse_fasta_document",
    "parse_experimental_design_table",
    "build_normalized_run_bundle",
    "build_fdr_audit_trail",
)

_ROOT_EXPORTS = {
    "DigestPolicy": ("bijux_proteomics.sequences.digestion", "DigestPolicy"),
    "parse_fasta_document": (
        "bijux_proteomics.sequences",
        "parse_fasta_document",
    ),
    "parse_experimental_design_table": (
        "bijux_proteomics.io.formats",
        "parse_experimental_design_table",
    ),
    "build_normalized_run_bundle": (
        "bijux_proteomics.io.formats",
        "build_normalized_run_bundle",
    ),
    "build_fdr_audit_trail": (
        "bijux_proteomics.identification",
        "build_fdr_audit_trail",
    ),
}


def __getattr__(name: str) -> Any:
    """Load public root exports lazily so package import stays dependency-light."""

    target = _ROOT_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
