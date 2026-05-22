# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    OrthologMappingCardinality,
    build_ortholog_mapping_report,
    parse_ortholog_table,
    parse_protein_reference_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_build_ortholog_mapping_report_classifies_ortholog_ambiguity() -> None:
    protein_table = parse_protein_reference_table(_fixture_path("ortholog_input.tsv"))
    ortholog_table = parse_ortholog_table(_fixture_path("ortholog_relationships.tsv"))

    report = build_ortholog_mapping_report(
        protein_table.accepted_entries,
        ortholog_table.accepted_records,
        source_species="HUMAN",
        target_species="mouse",
    )

    cardinalities = {
        (entry.source_protein_ref, entry.target_protein_ref): entry.mapping_cardinality
        for entry in report.mapped_entries
    }

    assert cardinalities[("P001", "M001")] == OrthologMappingCardinality.ONE_TO_ONE
    assert cardinalities[("P002", "M002")] == OrthologMappingCardinality.ONE_TO_MANY
    assert cardinalities[("P002", "M003")] == OrthologMappingCardinality.ONE_TO_MANY
    assert cardinalities[("P003", "M004")] == OrthologMappingCardinality.MANY_TO_ONE
    assert cardinalities[("P004", "M004")] == OrthologMappingCardinality.MANY_TO_ONE
    assert cardinalities[("P005", "M005")] == OrthologMappingCardinality.MANY_TO_MANY
    assert cardinalities[("P006", "M006")] == OrthologMappingCardinality.MANY_TO_MANY
    assert report.summary.one_to_many_count == 2
    assert report.summary.many_to_one_count == 2
    assert report.summary.many_to_many_count == 4
    assert report.summary.ambiguous_mapping_count == 8
