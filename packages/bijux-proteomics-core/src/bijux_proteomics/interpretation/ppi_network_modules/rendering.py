# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering surfaces for PPI network-module interpretation reports."""

from __future__ import annotations

import csv
from io import StringIO
import json

from .models import PpiEdgeImportReport, PpiNetworkModuleReport


def render_ppi_network_module_summary_tsv(report: PpiNetworkModuleReport) -> str:
    """Render the compact PPI network module summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "significant_protein_count",
            "retained_edge_count",
            "module_count",
            "isolated_protein_count",
            "largest_module_protein_count",
            "module_enrichment_count",
        )
    )
    writer.writerow(
        (
            report.summary.significant_protein_count,
            report.summary.retained_edge_count,
            report.summary.module_count,
            report.summary.isolated_protein_count,
            report.summary.largest_module_protein_count,
            report.summary.module_enrichment_count,
        )
    )
    return buffer.getvalue()


def render_ppi_network_edge_tsv(report: PpiNetworkModuleReport) -> str:
    """Render retained PPI subnetwork edges as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "module_id",
            "protein_ref_a",
            "protein_ref_b",
            "source_name",
            "source_accession",
            "interaction_score",
        )
    )
    for entry in report.edge_entries:
        writer.writerow(
            (
                entry.module_id,
                entry.protein_ref_a,
                entry.protein_ref_b,
                entry.source_name or "",
                entry.source_accession or "",
                ""
                if entry.interaction_score is None
                else f"{entry.interaction_score:g}",
            )
        )
    return buffer.getvalue()


def render_ppi_module_tsv(report: PpiNetworkModuleReport) -> str:
    """Render connected PPI modules as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("module_id", "protein_count", "edge_count", "hub_protein_refs", "protein_refs")
    )
    for entry in report.modules:
        writer.writerow(
            (
                entry.module_id,
                entry.protein_count,
                entry.edge_count,
                ";".join(entry.hub_protein_refs),
                ";".join(entry.protein_refs),
            )
        )
    return buffer.getvalue()


def render_ppi_isolated_protein_tsv(report: PpiNetworkModuleReport) -> str:
    """Render isolated significant proteins as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("protein_ref", "reason"))
    for entry in report.isolated_proteins:
        writer.writerow((entry.protein_ref, entry.reason))
    return buffer.getvalue()


def render_ppi_module_enrichment_tsv(report: PpiNetworkModuleReport) -> str:
    """Render optional module enrichment rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "module_id",
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            "foreground_overlap_count",
            "background_member_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
            "supporting_protein_refs",
        )
    )
    for entry in report.module_enrichments:
        writer.writerow(
            (
                entry.module_id,
                entry.set_id,
                entry.set_name or "",
                entry.set_category or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.foreground_overlap_count,
                entry.background_member_count,
                entry.foreground_size,
                entry.background_size,
                f"{entry.expected_overlap_count:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                ";".join(entry.supporting_protein_refs),
            )
        )
    return buffer.getvalue()


def render_rejected_ppi_edge_tsv(report: PpiEdgeImportReport) -> str:
    """Render rejected PPI edge rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(values, sort_keys=True)


__all__ = [
    "render_ppi_isolated_protein_tsv",
    "render_ppi_module_enrichment_tsv",
    "render_ppi_module_tsv",
    "render_ppi_network_edge_tsv",
    "render_ppi_network_module_summary_tsv",
    "render_rejected_ppi_edge_tsv",
]
