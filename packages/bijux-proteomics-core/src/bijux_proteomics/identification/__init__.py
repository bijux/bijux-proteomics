# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Identification evidence, confidence, and search-adapter surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics.identification._facade_runtime import build_facade_dir
from bijux_proteomics.identification.public_api import (
    build_facade_export_map,
    list_identification_adapter_api_modules,
    list_identification_contract_api_modules,
    list_identification_fdr_api_modules,
    list_identification_peptide_api_modules,
    list_identification_protein_api_modules,
    list_identification_psm_api_modules,
    merge_facade_export_maps,
)

_IDENTIFICATION_SUBMODULES = {
    "adapters": "bijux_proteomics.identification.adapters",
    "confidence": "bijux_proteomics.identification.confidence",
    "contracts": "bijux_proteomics.identification.contracts",
    "fdr": "bijux_proteomics.identification.fdr",
    "peptide": "bijux_proteomics.identification.peptide",
    "protein": "bijux_proteomics.identification.protein",
    "psm": "bijux_proteomics.identification.psm",
}

_IDENTIFICATION_EXPORT_OWNER_MAP = merge_facade_export_maps(
    build_facade_export_map(list_identification_adapter_api_modules()),
    build_facade_export_map(list_identification_contract_api_modules()),
    build_facade_export_map(list_identification_fdr_api_modules()),
    build_facade_export_map(list_identification_peptide_api_modules()),
    build_facade_export_map(list_identification_protein_api_modules()),
    build_facade_export_map(list_identification_psm_api_modules()),
)
_IDENTIFICATION_PUBLIC_EXPORTS = tuple(_IDENTIFICATION_EXPORT_OWNER_MAP)

__all__ = list(_IDENTIFICATION_PUBLIC_EXPORTS) + list(_IDENTIFICATION_SUBMODULES)


def __getattr__(name: str) -> Any:
    submodule_path = _IDENTIFICATION_SUBMODULES.get(name)
    if submodule_path is not None:
        module = import_module(submodule_path)
        globals()[name] = module
        return module
    owner_module = _IDENTIFICATION_EXPORT_OWNER_MAP.get(name)
    if owner_module is not None:
        module = import_module(owner_module)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return build_facade_dir(globals(), tuple(__all__))
