# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned report contracts for PPI subnetwork and module interpretation."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PpiEdgeColumnMapping(JsonModel):
    """Column mapping from one PPI edge table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref_a: str = Field(..., min_length=1)
    protein_ref_b: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    interaction_score: str | None = None


class PpiEdgeRecord(JsonModel):
    """One normalized undirected PPI edge."""

    model_config = ConfigDict(extra="forbid")

    protein_ref_a: str = Field(..., min_length=1)
    protein_ref_b: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    interaction_score: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedPpiEdgeRow(JsonModel):
    """One rejected PPI edge row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class PpiEdgeImportSummary(JsonModel):
    """Stable summary over one PPI edge import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_count: int = Field(..., ge=0)
    source_counts: dict[str, int] = Field(default_factory=dict)


class PpiEdgeImportReport(JsonModel):
    """Governed import report over one PPI edge table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PpiEdgeRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPpiEdgeRow, ...] = Field(default_factory=tuple)
    column_mapping: PpiEdgeColumnMapping
    summary: PpiEdgeImportSummary
    note: str = Field(..., min_length=1)


class PpiSubnetworkEdgeEntry(JsonModel):
    """One retained PPI edge between significant proteins."""

    model_config = ConfigDict(extra="forbid")

    module_id: str = Field(..., min_length=1)
    protein_ref_a: str = Field(..., min_length=1)
    protein_ref_b: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    interaction_score: float | None = None


class PpiModuleEntry(JsonModel):
    """One connected PPI module with hub metadata."""

    model_config = ConfigDict(extra="forbid")

    module_id: str = Field(..., min_length=1)
    protein_count: int = Field(..., ge=2)
    edge_count: int = Field(..., ge=1)
    hub_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class PpiIsolatedProteinEntry(JsonModel):
    """One significant protein that did not participate in any retained module edge."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class PpiModuleEnrichmentEntry(JsonModel):
    """One enrichment row attached to one connected PPI module."""

    model_config = ConfigDict(extra="forbid")

    module_id: str = Field(..., min_length=1)
    set_id: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    foreground_overlap_count: int = Field(..., ge=0)
    background_member_count: int = Field(..., ge=0)
    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    expected_overlap_count: float = Field(..., ge=0.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class PpiNetworkModuleSummary(JsonModel):
    """Stable summary over one PPI subnetwork and module run."""

    model_config = ConfigDict(extra="forbid")

    significant_protein_count: int = Field(..., ge=0)
    retained_edge_count: int = Field(..., ge=0)
    module_count: int = Field(..., ge=0)
    isolated_protein_count: int = Field(..., ge=0)
    largest_module_protein_count: int = Field(..., ge=0)
    module_enrichment_count: int = Field(..., ge=0)


class PpiNetworkModuleReport(JsonModel):
    """Owned PPI subnetwork and connected-module report over significant proteins."""

    model_config = ConfigDict(extra="forbid")

    edge_entries: tuple[PpiSubnetworkEdgeEntry, ...] = Field(default_factory=tuple)
    modules: tuple[PpiModuleEntry, ...] = Field(default_factory=tuple)
    isolated_proteins: tuple[PpiIsolatedProteinEntry, ...] = Field(
        default_factory=tuple
    )
    module_enrichments: tuple[PpiModuleEnrichmentEntry, ...] = Field(
        default_factory=tuple
    )
    summary: PpiNetworkModuleSummary
    note: str = Field(..., min_length=1)


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
]
