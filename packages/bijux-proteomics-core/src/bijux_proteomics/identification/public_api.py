"""Machine-readable public facade contract for identification owner packages."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    build_facade_export_map,
    build_facade_module as _module,
    flatten_facade_exports,
    merge_facade_export_maps,
)
from bijux_proteomics.identification.facade_ledger.peptide import (
    PEPTIDE_FACADE_BUDGET,
    list_identification_peptide_api_modules,
)
from bijux_proteomics.identification.facade_ledger.protein import (
    PROTEIN_FACADE_BUDGET,
    list_identification_protein_api_modules,
)
from bijux_proteomics.identification.facade_ledger.psm import (
    PSM_FACADE_BUDGET,
    list_identification_psm_api_modules,
)
from bijux_proteomics.identification.facade_ledger.fdr import (
    FDR_FACADE_BUDGET,
    list_identification_fdr_api_modules,
)
from bijux_proteomics.identification.facade_ledger.contracts import (
    CONTRACTS_FACADE_BUDGET,
    list_identification_contract_api_modules,
)
from bijux_proteomics.identification.facade_ledger.adapters import (
    ADAPTERS_FACADE_BUDGET,
    list_identification_adapter_api_modules,
)

IDENTIFICATION_OWNER_SUBMODULE_NAMES = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)
IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES = ("confidence",)
IDENTIFICATION_ROOT_FACADE_ORDER = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)


__all__ = [
    "ADAPTERS_FACADE_BUDGET",
    "IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES",
    "IDENTIFICATION_ROOT_FACADE_ORDER",
    "CONTRACTS_FACADE_BUDGET",
    "FDR_FACADE_BUDGET",
    "IDENTIFICATION_OWNER_SUBMODULE_NAMES",
    "PEPTIDE_FACADE_BUDGET",
    "PROTEIN_FACADE_BUDGET",
    "PSM_FACADE_BUDGET",
    "IdentificationFacadeBudget",
    "IdentificationFacadeModule",
    "build_facade_export_map",
    "merge_facade_export_maps",
    "flatten_facade_exports",
    "list_identification_adapter_api_modules",
    "list_identification_contract_api_modules",
    "list_identification_fdr_api_modules",
    "list_identification_peptide_api_modules",
    "list_identification_protein_api_modules",
    "list_identification_psm_api_modules",
]
