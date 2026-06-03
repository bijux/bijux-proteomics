# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biological interpretation and downstream annotation surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_INTERPRETATION_EXPORT_MODULES = (
    "bijux_proteomics.interpretation.biological_context_mapping",
    "bijux_proteomics.interpretation.annotation_packs",
    "bijux_proteomics.interpretation.compartment_biology",
    "bijux_proteomics.interpretation.complex_activity",
    "bijux_proteomics.interpretation.complex_enrichment",
    "bijux_proteomics.interpretation.drug_target_interpretation",
    "bijux_proteomics.interpretation.disease_phenotype_interpretation",
    "bijux_proteomics.interpretation.foreground_background_model",
    "bijux_proteomics.interpretation.go_enrichment",
    "bijux_proteomics.interpretation.ortholog_mapping",
    "bijux_proteomics.interpretation.pathway_activity",
    "bijux_proteomics.interpretation.pathway_enrichment",
    "bijux_proteomics.interpretation.ppi_network_modules",
    "bijux_proteomics.interpretation.protein_annotation_mapping",
    "bijux_proteomics.interpretation.regulator_inference",
    "bijux_proteomics.interpretation.protein_set_enrichment",
    "bijux_proteomics.interpretation.protein_set_scoring",
    "bijux_proteomics.interpretation.tissue_cell_type_context",
)


def __getattr__(name: str) -> Any:
    for module_path in _INTERPRETATION_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
