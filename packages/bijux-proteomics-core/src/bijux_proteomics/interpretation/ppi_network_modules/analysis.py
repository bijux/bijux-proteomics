# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PPI subnetwork and connected-module surfaces for biological interpretation."""

from __future__ import annotations

from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.interpretation.protein_set_enrichment import (
    ProteinSetEnrichmentPolicy,
    build_protein_set_enrichment_report,
)
from bijux_proteomics.interpretation.protein_set_scoring import ProteinSetRecord

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


def build_ppi_network_module_report(
    significant_entries: tuple[ProteinReferenceEntry, ...],
    edge_records: tuple[PpiEdgeRecord, ...],
    *,
    protein_set_records: tuple[ProteinSetRecord, ...] = (),
    enrichment_policy: ProteinSetEnrichmentPolicy | None = None,
) -> PpiNetworkModuleReport:
    """Build the retained PPI subnetwork, connected modules, and optional module enrichment."""

    significant_proteins = tuple(
        sorted({entry.protein_ref for entry in significant_entries})
    )
    if not significant_proteins:
        raise ValueError("significant protein set must contain at least one protein")

    significant_lookup = set(significant_proteins)
    retained_edges = tuple(
        record
        for record in edge_records
        if record.protein_ref_a in significant_lookup
        and record.protein_ref_b in significant_lookup
    )
    adjacency: dict[str, set[str]] = {
        protein_ref: set() for protein_ref in significant_proteins
    }
    for edge in retained_edges:
        adjacency[edge.protein_ref_a].add(edge.protein_ref_b)
        adjacency[edge.protein_ref_b].add(edge.protein_ref_a)

    components = _connected_components(adjacency)
    module_members = tuple(component for component in components if len(component) > 1)
    isolated_members = tuple(
        component[0] for component in components if len(component) == 1
    )

    module_entries: list[PpiModuleEntry] = []
    edge_entries: list[PpiSubnetworkEdgeEntry] = []
    module_enrichments: list[PpiModuleEnrichmentEntry] = []
    module_index_by_protein: dict[str, str] = {}
    for members in sorted(module_members, key=lambda entry: (-len(entry), entry)):
        module_id = _module_id(members)
        for protein_ref in members:
            module_index_by_protein[protein_ref] = module_id
        module_edges = tuple(
            edge
            for edge in retained_edges
            if edge.protein_ref_a in members and edge.protein_ref_b in members
        )
        hub_protein_refs = _hub_proteins(members, adjacency)
        module_entries.append(
            PpiModuleEntry(
                module_id=module_id,
                protein_count=len(members),
                edge_count=len(module_edges),
                hub_protein_refs=hub_protein_refs,
                protein_refs=members,
            )
        )
        for edge in module_edges:
            edge_entries.append(
                PpiSubnetworkEdgeEntry(
                    module_id=module_id,
                    protein_ref_a=edge.protein_ref_a,
                    protein_ref_b=edge.protein_ref_b,
                    source_name=edge.source_name,
                    source_accession=edge.source_accession,
                    interaction_score=edge.interaction_score,
                )
            )
        if protein_set_records:
            enrichment_report = build_protein_set_enrichment_report(
                tuple(
                    ProteinReferenceEntry(
                        row_number=index + 2,
                        source_row_id=f"{module_id}:{protein_ref}",
                        input_protein_ref=protein_ref,
                        protein_ref=protein_ref,
                    )
                    for index, protein_ref in enumerate(members)
                ),
                protein_set_records,
                background_entries=tuple(
                    ProteinReferenceEntry(
                        row_number=index + 2,
                        source_row_id=f"background:{protein_ref}",
                        input_protein_ref=protein_ref,
                        protein_ref=protein_ref,
                    )
                    for index, protein_ref in enumerate(significant_proteins)
                ),
                policy=enrichment_policy
                or ProteinSetEnrichmentPolicy(
                    max_adjusted_p_value=1.0,
                    min_enrichment_ratio=0.0,
                ),
            )
            for entry in enrichment_report.entries:
                module_enrichments.append(
                    PpiModuleEnrichmentEntry(
                        module_id=module_id,
                        set_id=entry.set_id,
                        set_name=entry.set_name,
                        set_category=entry.set_category,
                        source_name=entry.source_name,
                        source_accession=entry.source_accession,
                        foreground_overlap_count=entry.foreground_overlap_count,
                        background_member_count=entry.background_member_count,
                        foreground_size=entry.foreground_size,
                        background_size=entry.background_size,
                        expected_overlap_count=entry.expected_overlap_count,
                        enrichment_ratio=entry.enrichment_ratio,
                        p_value=entry.p_value,
                        adjusted_p_value=entry.adjusted_p_value,
                        supporting_protein_refs=entry.supporting_protein_refs,
                    )
                )

    isolated_entries = tuple(
        PpiIsolatedProteinEntry(
            protein_ref=protein_ref,
            reason="significant protein had no retained ppi edge and was not assigned to a module",
        )
        for protein_ref in isolated_members
    )
    return PpiNetworkModuleReport(
        edge_entries=tuple(
            sorted(
                edge_entries,
                key=lambda entry: (
                    entry.module_id,
                    entry.protein_ref_a,
                    entry.protein_ref_b,
                ),
            )
        ),
        modules=tuple(module_entries),
        isolated_proteins=isolated_entries,
        module_enrichments=tuple(
            sorted(
                module_enrichments,
                key=lambda entry: (
                    entry.module_id,
                    entry.adjusted_p_value
                    if entry.adjusted_p_value is not None
                    else 1.0,
                    entry.set_id,
                ),
            )
        ),
        summary=PpiNetworkModuleSummary(
            significant_protein_count=len(significant_proteins),
            retained_edge_count=len(retained_edges),
            module_count=len(module_entries),
            isolated_protein_count=len(isolated_entries),
            largest_module_protein_count=max(
                (entry.protein_count for entry in module_entries),
                default=0,
            ),
            module_enrichment_count=len(module_enrichments),
        ),
        note=(
            "ppi module detection keeps only interactions between significant proteins, "
            "reports connected components with two or more proteins as modules, and preserves isolated proteins explicitly"
        ),
    )


def _connected_components(
    adjacency: dict[str, set[str]],
) -> tuple[tuple[str, ...], ...]:
    visited: set[str] = set()
    components: list[tuple[str, ...]] = []
    for protein_ref in sorted(adjacency):
        if protein_ref in visited:
            continue
        stack = [protein_ref]
        component: list[str] = []
        visited.add(protein_ref)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(components)


def _hub_proteins(
    members: tuple[str, ...],
    adjacency: dict[str, set[str]],
) -> tuple[str, ...]:
    degree_by_protein = {
        protein_ref: len(adjacency[protein_ref]) for protein_ref in members
    }
    max_degree = max(degree_by_protein.values(), default=0)
    return tuple(
        protein_ref
        for protein_ref in sorted(members)
        if degree_by_protein[protein_ref] == max_degree
    )


def _module_id(members: tuple[str, ...]) -> str:
    return "ppi_module:" + ",".join(members)


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
]
