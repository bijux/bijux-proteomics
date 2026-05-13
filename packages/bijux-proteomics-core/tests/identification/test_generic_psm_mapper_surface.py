# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.identification.generic_psm_mapper import (
    GenericPsmTableColumnMapping,
    build_generic_psm_mapper_report,
    load_generic_psm_table_mapping,
    render_generic_psm_mapper_tsv,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "search_adapters" / name
    )


def test_generic_psm_mapper_loads_yaml_and_json_column_maps() -> None:
    json_mapping = load_generic_psm_table_mapping(_fixture("generic_mapper_mapping.json"))
    yaml_mapping = load_generic_psm_table_mapping(_fixture("generic_mapper_mapping.yaml"))

    assert json_mapping == yaml_mapping
    assert json_mapping.run_id == "run_name"
    assert json_mapping.q_value == "qvalue"


def test_generic_psm_mapper_report_preserves_run_mapping_and_unmapped_columns() -> None:
    report = build_generic_psm_mapper_report(
        _fixture("generic_mapper_results.tsv"),
        mapping_path=_fixture("generic_mapper_mapping.yaml"),
    )

    assert report.summary.total_rows == 2
    assert report.summary.accepted_rows == 2
    assert report.summary.rejected_rows == 0
    assert report.summary.mapped_run_count == 2
    assert report.summary.q_value_row_count == 2
    assert report.summary.protein_mapped_row_count == 2
    assert report.summary.unmapped_source_column_count == 2
    assert report.summary.unmapped_source_columns == ("analyst_note", "instrument")
    assert report.normalization.adapter_manifest.adapter_kind.value == "generic"
    assert report.mapped_rows[0].run_id == "run_A"
    assert report.mapped_rows[0].spectrum_id == "generic-1001"
    assert report.mapped_rows[1].target_decoy_label.value == "decoy"
    assert "run_id" in render_generic_psm_mapper_tsv(report.mapped_rows)


def test_generic_psm_mapper_rejects_unsupported_mapping_extensions() -> None:
    with pytest.raises(ValueError, match="must use \\.json, \\.yaml, or \\.yml"):
        load_generic_psm_table_mapping(_fixture("generic_results.tsv"))


def test_generic_psm_mapper_requires_core_field_mappings() -> None:
    with pytest.raises(ValueError):
        GenericPsmTableColumnMapping.model_validate(
            {
                "run_id": "run_name",
                "spectrum_id": "scan_ref",
                "peptide": "sequence_text",
                "charge": "z",
            }
        )
