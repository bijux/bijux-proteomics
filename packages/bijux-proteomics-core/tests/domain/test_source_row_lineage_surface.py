# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.domain import SourceRowLineage
from bijux_proteomics.domain.records import ImportedEvidenceProvenance


def test_source_row_lineage_normalizes_exact_refs() -> None:
    lineage = SourceRowLineage.from_source_row_refs(
        (" protein_stats.tsv:4 ", "protein_stats.tsv:4", "protein_matrix.tsv:9")
    )

    assert lineage.source_row_refs == ("protein_stats.tsv:4", "protein_matrix.tsv:9")
    assert lineage.derived_no_source_reason is None
    assert lineage.source_row_chain == "protein_stats.tsv:4;protein_matrix.tsv:9"


def test_source_row_lineage_builds_exact_refs_from_imported_provenance() -> None:
    lineage = SourceRowLineage.from_imported_provenances(
        (
            ImportedEvidenceProvenance(
                source_engine="maxquant",
                source_files=("evidence.tsv",),
                source_row_numbers=(7, 12),
                original_identifiers={"scan": "scan=101"},
            ),
            ImportedEvidenceProvenance(
                source_engine="maxquant",
                source_files=("protein_groups.tsv",),
                source_row_numbers=(3,),
                original_identifiers={"protein_group_id": "PG001"},
            ),
        )
    )

    assert lineage.source_row_refs == (
        "evidence.tsv:7",
        "evidence.tsv:12",
        "protein_groups.tsv:3",
    )


def test_source_row_lineage_rejects_missing_refs_and_missing_reason() -> None:
    with pytest.raises(ValueError, match="requires concrete refs or an explicit"):
        SourceRowLineage()


def test_source_row_lineage_rejects_refs_and_reason_together() -> None:
    with pytest.raises(ValueError, match="not both"):
        SourceRowLineage(
            source_row_refs=("protein_stats.tsv:4",),
            derived_no_source_reason="aggregated comparison",
        )
