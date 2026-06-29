# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PPI subnetwork and connected-module surfaces for biological interpretation."""

from __future__ import annotations

from .analysis import (
    build_ppi_network_module_report,
    parse_ppi_edge_table,
)
from .models import (
    PpiEdgeColumnMapping,
    PpiEdgeImportReport,
    PpiEdgeImportSummary,
    PpiEdgeRecord,
    PpiIsolatedProteinEntry,
    PpiModuleEnrichmentEntry,
    PpiModuleEntry,
    PpiNetworkModuleReport,
    PpiNetworkModuleSummary,
    PpiSubnetworkEdgeEntry,
    RejectedPpiEdgeRow,
)
from .rendering import (
    render_ppi_isolated_protein_tsv,
    render_ppi_module_enrichment_tsv,
    render_ppi_module_tsv,
    render_ppi_network_edge_tsv,
    render_ppi_network_module_summary_tsv,
    render_rejected_ppi_edge_tsv,
)

__all__ = [
    "PpiEdgeColumnMapping",
    "PpiEdgeImportReport",
    "PpiEdgeImportSummary",
    "PpiEdgeRecord",
    "PpiIsolatedProteinEntry",
    "PpiModuleEnrichmentEntry",
    "PpiModuleEntry",
    "PpiNetworkModuleReport",
    "PpiNetworkModuleSummary",
    "PpiSubnetworkEdgeEntry",
    "RejectedPpiEdgeRow",
    "build_ppi_network_module_report",
    "parse_ppi_edge_table",
    "render_ppi_isolated_protein_tsv",
    "render_ppi_module_enrichment_tsv",
    "render_ppi_module_tsv",
    "render_ppi_network_edge_tsv",
    "render_ppi_network_module_summary_tsv",
    "render_rejected_ppi_edge_tsv",
]
