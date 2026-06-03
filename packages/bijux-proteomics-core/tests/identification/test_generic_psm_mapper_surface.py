# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.identification.generic_psm_mapper import (
    build_generic_psm_mapper_report,
    load_generic_psm_table_mapping,
    render_generic_psm_mapper_tsv,
    render_generic_psm_rejected_row_tsv,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "search_adapters" / name
    )


def test_generic_psm_mapper_loads_yaml_and_json_column_maps() -> None:
    json_mapping = load_generic_psm_table_mapping(
        _fixture("generic_mapper_mapping.json")
    )
    yaml_mapping = load_generic_psm_table_mapping(
        _fixture("generic_mapper_mapping.yaml")
    )

    assert json_mapping == yaml_mapping
    assert json_mapping.run_id == "run_name"
    assert json_mapping.modified_peptide == "modified_sequence"
    assert json_mapping.score_orientation == "higher_better"
    assert json_mapping.intensity == "precursor_intensity"
    assert json_mapping.q_value == "qvalue"
    assert json_mapping.contaminant_label == "contaminant_state"


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
    assert report.column_mapping.score_orientation == "higher_better"
    assert report.normalization.adapter_manifest.adapter_kind.value == "generic"
    assert (
        report.normalization.adapter_manifest.score_orientation.value == "higher_better"
    )
    assert report.mapped_rows[0].run_id == "run_A"
    assert report.mapped_rows[0].spectrum_id == "generic-1001"
    assert report.mapped_rows[0].peptide_sequence == "PESTIDE"
    assert report.mapped_rows[0].modified_peptide == "PES[Phospho]TIDE"
    assert report.mapped_rows[0].intensity == 125000.0
    assert report.mapped_rows[0].provenance is not None
    assert report.mapped_rows[0].provenance.source_engine == "generic"
    assert report.mapped_rows[0].provenance.source_row_numbers == (2,)
    assert report.mapped_rows[0].provenance.original_identifiers["spectrum_id"] == (
        "generic-1001"
    )
    assert report.mapped_rows[1].target_decoy_label.value == "decoy"
    assert report.mapped_rows[1].target_decoy_contaminant_class.value == "mixed"
    assert report.mapped_rows[1].contaminant_flag is True
    assert "run_id" in render_generic_psm_mapper_tsv(report.mapped_rows)
    assert "intensity" in render_generic_psm_mapper_tsv(report.mapped_rows)
    assert "modified_peptide" in render_generic_psm_mapper_tsv(report.mapped_rows)
    assert "source_engine" in render_generic_psm_mapper_tsv(report.mapped_rows)
    assert "source_file" in render_generic_psm_mapper_tsv(report.mapped_rows)
    assert "original_identifiers" in render_generic_psm_mapper_tsv(report.mapped_rows)
    assert "target_decoy_contaminant_class" in render_generic_psm_mapper_tsv(
        report.mapped_rows
    )


def test_generic_psm_mapper_supports_modified_only_mapping_and_explicit_orientation(
    tmp_path: Path,
) -> None:
    mapping_path = tmp_path / "modified_only_mapping.yaml"
    mapping_path.write_text(
        "\n".join(
            (
                "run_id: run_name",
                "spectrum_id: scan_ref",
                "modified_peptide: modified_sequence",
                "charge: z",
                "score: state_score",
                "score_orientation: lower_better",
                "protein_refs: accessions",
                "decoy_label: decoy_state",
                "contaminant_label: contaminant_state",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_generic_psm_mapper_report(
        _fixture("generic_mapper_results.tsv"),
        mapping_path=mapping_path,
    )

    assert report.summary.accepted_rows == 2
    assert (
        report.normalization.adapter_manifest.score_orientation.value == "lower_better"
    )
    assert report.mapped_rows[0].canonical_peptide == "PES[Phospho]TIDE"


def test_generic_psm_mapper_rejects_unsupported_mapping_extensions() -> None:
    with pytest.raises(ValueError, match="must use \\.json, \\.yaml, or \\.yml"):
        load_generic_psm_table_mapping(_fixture("generic_results.tsv"))


def test_generic_psm_mapper_missing_required_mapping_blocks_import(
    tmp_path: Path,
) -> None:
    missing_orientation = tmp_path / "missing_orientation.yaml"
    missing_orientation.write_text(
        "\n".join(
            (
                "run_id: run_name",
                "spectrum_id: scan_ref",
                "peptide: sequence_text",
                "charge: z",
                "score: state_score",
                "protein_refs: accessions",
                "decoy_label: decoy_state",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    missing_decoy_rule = tmp_path / "missing_decoy_rule.yaml"
    missing_decoy_rule.write_text(
        "\n".join(
            (
                "run_id: run_name",
                "spectrum_id: scan_ref",
                "modified_peptide: modified_sequence",
                "charge: z",
                "score: state_score",
                "score_orientation: higher_better",
                "protein_refs: accessions",
                "decoy_prefix:",
                "decoy_suffix:",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="score_orientation"):
        build_generic_psm_mapper_report(
            _fixture("generic_mapper_results.tsv"),
            mapping_path=missing_orientation,
        )
    with pytest.raises(ValueError, match="decoy label column or decoy naming rule"):
        build_generic_psm_mapper_report(
            _fixture("generic_mapper_results.tsv"),
            mapping_path=missing_decoy_rule,
        )


def test_generic_psm_mapper_rejected_rows_render_stably(tmp_path: Path) -> None:
    input_path = tmp_path / "generic_mapper_invalid.tsv"
    input_path.write_text(
        "\n".join(
            (
                "run_name\tscan_ref\tsequence_text\tmodified_sequence\tz\tstate_score\tprecursor_intensity\tqvalue\taccessions\tdecoy_state\tcontaminant_state\tinstrument\tanalyst_note",
                "run_A\tgeneric-1001\tPESTIDE\tPES[Phospho]TIDE\t2\t55.0\t125000\t0.002\tP12345\ttarget\tfalse\torbitrap\tstable",
                "run_B\tgeneric-1002\tBROKEN\tBROKEN\tbad\t12.0\t4300\t0.05\tCON__P54321\tdecoy\tcontaminant\ttof\treview",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_generic_psm_mapper_report(
        input_path,
        mapping_path=_fixture("generic_mapper_mapping.yaml"),
    )

    assert report.summary.accepted_rows == 1
    assert report.summary.rejected_rows == 1
    assert report.rejected_rows[0].issues[0].code == "invalid_charge"
    assert len(report.rejected_evidence_rows) == 1
    assert report.rejected_evidence_rows[0].source_file == "generic_mapper_invalid.tsv"
    assert report.rejected_evidence_rows[0].entity_type == "psm"
    assert report.rejected_evidence_rows[0].entity_id == "generic-1002"
    assert report.rejected_evidence_rows[0].reason_code == "invalid_charge"
    assert "raw_fields_json" in render_generic_psm_rejected_row_tsv(
        report.rejected_rows
    )
