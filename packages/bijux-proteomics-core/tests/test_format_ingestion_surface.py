# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    FormatConversionTarget,
    ProteomicsFormatKind,
    build_mzml_collection_summary,
    build_normalized_run_bundle,
    convert_proteomics_format,
    detect_proteomics_format,
    extract_mzml_metadata,
    parse_experimental_design_table,
    parse_mzml,
    stream_mzml_spectra,
    validate_proteomics_input,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "first_useful_run" / name


def test_mzml_reader_and_metadata_extract_stable_spectrum_contracts() -> None:
    report = parse_mzml(_format_fixture("simple.mzml"))
    metadata = extract_mzml_metadata(_format_fixture("simple.mzml"))
    streamed = tuple(stream_mzml_spectra(_format_fixture("simple.mzml")))
    summary = build_mzml_collection_summary(report)

    assert report.total_spectra == 2
    assert len(report.accepted_spectra) == 2
    assert not report.rejected_spectra
    assert metadata.run_id == "RUN_001"
    assert metadata.start_time_iso == "2026-04-29T10:00:00Z"
    assert metadata.instrument_names == ("Q Exactive",)
    assert streamed[0].spectrum_id == "scan=5001"
    assert streamed[1].precursor_charge == 3
    assert summary.spectrum_count == 2
    assert summary.issue_counts == {}


def test_mzml_validation_catches_binary_array_length_mismatches() -> None:
    report = parse_mzml(_format_fixture("malformed_lengths.mzml"))
    validation = validate_proteomics_input(
        _format_fixture("malformed_lengths.mzml"),
        input_kind=ProteomicsFormatKind.MZML,
    )

    assert len(report.accepted_spectra) == 0
    assert len(report.rejected_spectra) == 1
    codes = {issue.code for issue in report.rejected_spectra[0].issues}
    assert "array_length_mismatch" in codes
    assert "peak_array_length_mismatch" in codes
    assert validation.valid is False
    assert {issue.code for issue in validation.issues} >= {
        "array_length_mismatch",
        "peak_array_length_mismatch",
    }


def test_format_detection_and_design_table_parsing_are_stable() -> None:
    design_report = parse_experimental_design_table(_format_fixture("valid.design.tsv"))
    invalid_design = validate_proteomics_input(
        _format_fixture("invalid.design.tsv"),
        input_kind=ProteomicsFormatKind.DESIGN_TABLE,
    )

    assert (
        detect_proteomics_format(_format_fixture("simple.mzml"))
        is ProteomicsFormatKind.MZML
    )
    assert (
        detect_proteomics_format(_format_fixture("valid.design.tsv"))
        is ProteomicsFormatKind.DESIGN_TABLE
    )
    assert (
        detect_proteomics_format(_workflow_fixture("results.tsv"))
        is ProteomicsFormatKind.PSM
    )
    assert len(design_report.accepted_entries) == 1
    assert design_report.accepted_entries[0].search_engine == "Sage"
    assert invalid_design.valid is False
    assert invalid_design.summary["rejected_rows"] == 1


def test_format_conversion_and_run_bundle_outputs_are_stable(tmp_path: Path) -> None:
    mgf_output = tmp_path / "from_mzml.mgf"
    jsonl_output = tmp_path / "spectra.jsonl"
    bundle_dir = tmp_path / "bundle"

    mgf_conversion = convert_proteomics_format(
        input_path=_format_fixture("simple.mzml"),
        output_path=mgf_output,
        input_kind=ProteomicsFormatKind.MZML,
        target_format=FormatConversionTarget.MGF,
    )
    spectra_conversion = convert_proteomics_format(
        input_path=_format_fixture("simple.mzml"),
        output_path=jsonl_output,
        input_kind=ProteomicsFormatKind.MZML,
        target_format=FormatConversionTarget.SPECTRA_JSONL,
    )
    manifest = build_normalized_run_bundle(
        bundle_dir=bundle_dir,
        spectra_path=_format_fixture("simple.mzml"),
        identifications_path=_workflow_fixture("results.tsv"),
        design_path=_format_fixture("valid.design.tsv"),
    )

    assert mgf_conversion.written_record_count == 2
    assert "BEGIN IONS" in mgf_output.read_text()
    assert spectra_conversion.written_record_count == 2
    assert len(jsonl_output.read_text().splitlines()) == 2
    assert manifest.spectrum_count == 2
    assert manifest.psm_count == 2
    assert manifest.metadata.instrument == "Q Exactive"
    assert (bundle_dir / "bundle.manifest.json").exists()
    generated = json.loads((bundle_dir / "bundle.manifest.json").read_text())
    assert (
        generated["document_schema"]["document_kind"]
        == "normalized_proteomics_run_bundle"
    )
    assert "spectra.normalized.mgf" in generated["generated_files"]
