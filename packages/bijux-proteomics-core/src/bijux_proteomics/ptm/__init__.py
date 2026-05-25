# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM evidence, proteoform, and laboratory-review surfaces."""

from __future__ import annotations

from importlib import import_module

_PTM_EXPORT_MODULES = (
    "bijux_proteomics.ptm.contracts",
    "bijux_proteomics.ptm.abundance_correction",
    "bijux_proteomics.ptm.crosstalk",
    "bijux_proteomics.ptm.differential_analysis",
    "bijux_proteomics.ptm.localization_scoring",
    "bijux_proteomics.ptm.motif_analysis",
    "bijux_proteomics.ptm.occupancy_estimation",
    "bijux_proteomics.ptm.peptide_parser",
    "bijux_proteomics.ptm.protein_site_mapping",
    "bijux_proteomics.ptm.regulator_enrichment",
    "bijux_proteomics.ptm.ambiguity_handling",
    "bijux_proteomics.ptm.acetylation",
    "bijux_proteomics.ptm.context_annotation",
    "bijux_proteomics.ptm.evidence_cards",
    "bijux_proteomics.ptm.fragment_scoring",
    "bijux_proteomics.ptm.hotspots",
    "bijux_proteomics.ptm.kinase_inference",
    "bijux_proteomics.ptm.localization_risk",
    "bijux_proteomics.ptm.mechanism_classification",
    "bijux_proteomics.ptm.ortholog_site_conservation",
    "bijux_proteomics.ptm.oxidation",
    "bijux_proteomics.ptm.reporting",
    "bijux_proteomics.ptm.phosphatase_inference",
    "bijux_proteomics.ptm.site_quantification",
    "bijux_proteomics.ptm.proteoforms",
    "bijux_proteomics.ptm.review",
    "bijux_proteomics.ptm.site_annotation_import",
    "bijux_proteomics.ptm.site_groups",
)


def __getattr__(name: str) -> object:
    for module_path in _PTM_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
