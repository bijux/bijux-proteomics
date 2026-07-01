# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for cross-study protein harmonization reports."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from bijux_proteomics.workflow.studies.cross_study.tsv_support import export_tsv_table

if TYPE_CHECKING:
    from bijux_proteomics.workflow.studies.cross_study.protein_harmonization import (
        CrossStudyProteinHarmonizationReport,
    )


def render_cross_study_protein_harmonization_tsv(
    report: CrossStudyProteinHarmonizationReport,
) -> str:
    """Render harmonized cross-study protein memberships as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "source_kind",
            "source_surface",
            "source_entity_id",
            "representative_protein_ref",
            "protein_refs",
            "accession_aliases",
            "gene_symbol",
            "match_basis",
            "harmonized_study_count",
            "note",
        ]
    )
    for entry in report.harmonized_entries:
        writer.writerow(
            [
                entry.harmonized_id,
                entry.observation_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.source_kind.value,
                entry.source_surface,
                entry.source_entity_id,
                entry.representative_protein_ref,
                ";".join(entry.protein_refs),
                ";".join(entry.accession_aliases),
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.match_basis.value,
                entry.harmonized_study_count,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_protein_unresolved_tsv(
    report: CrossStudyProteinHarmonizationReport,
) -> str:
    """Render unresolved cross-study protein identities as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "source_kind",
            "source_surface",
            "source_entity_id",
            "representative_protein_ref",
            "protein_refs",
            "accession_aliases",
            "gene_symbol",
            "reason",
            "candidate_observation_ids",
            "candidate_study_ids",
            "note",
        ]
    )
    for entry in report.unresolved_entries:
        writer.writerow(
            [
                entry.observation_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.source_kind.value,
                entry.source_surface,
                entry.source_entity_id,
                entry.representative_protein_ref,
                ";".join(entry.protein_refs),
                ";".join(entry.accession_aliases),
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.reason.value,
                ";".join(entry.candidate_observation_ids),
                ";".join(entry.candidate_study_ids),
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_cross_study_protein_harmonization_tsv(
    report: CrossStudyProteinHarmonizationReport,
    path: Path,
) -> None:
    """Write harmonized cross-study protein memberships to a TSV artifact."""
    export_tsv_table(path, render_cross_study_protein_harmonization_tsv(report))


def export_cross_study_protein_unresolved_tsv(
    report: CrossStudyProteinHarmonizationReport,
    path: Path,
) -> None:
    """Write unresolved cross-study protein identities to a TSV artifact."""
    export_tsv_table(path, render_cross_study_protein_unresolved_tsv(report))


__all__ = [
    "export_cross_study_protein_harmonization_tsv",
    "export_cross_study_protein_unresolved_tsv",
    "render_cross_study_protein_harmonization_tsv",
    "render_cross_study_protein_unresolved_tsv",
]
