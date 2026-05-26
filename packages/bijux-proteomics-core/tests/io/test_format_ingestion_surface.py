# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.io.formats import (
    ExperimentalDesignSampleRole,
    FormatConversionTarget,
    ProteomicsFormatKind,
    build_mzml_collection_summary,
    build_normalized_run_bundle,
    convert_proteomics_format,
    detect_proteomics_format,
    diagnose_proteomics_format,
    extract_mzml_metadata,
    parse_experimental_design_table,
    parse_mzml,
    stream_mzml_spectra,
    validate_proteomics_input,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "first_useful_run" / name


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
    assert streamed[0].native_id == "scan=5001"
    assert streamed[0].scan_number == 5001
    assert streamed[0].ms_level == 2
    assert streamed[0].parent_spectrum_id == "scan=5000"
    assert streamed[1].precursor_charge == 3
    assert summary.spectrum_count == 2
    assert summary.issue_counts == {}


def test_mzml_scan_hierarchy_preserves_precursor_and_product_relationships() -> None:
    report = parse_mzml(_format_fixture("hierarchy.mzml"))

    assert len(report.accepted_spectra) == 1
    spectrum = report.accepted_spectra[0]
    assert spectrum.native_id == "controllerType=0 controllerNumber=1 scan=8101"
    assert spectrum.scan_number == 8101
    assert spectrum.ms_level == 2
    assert (
        spectrum.parent_spectrum_id == "controllerType=0 controllerNumber=1 scan=8100"
    )
    assert spectrum.product_isolation_mz == 175.1


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


def test_mzml_validation_rejects_unsupported_binary_compression_and_precision() -> None:
    numpress_report = parse_mzml(_format_fixture("unsupported_numpress.mzml"))
    numpress_validation = validate_proteomics_input(
        _format_fixture("unsupported_numpress.mzml"),
        input_kind=ProteomicsFormatKind.MZML,
    )
    integer_report = parse_mzml(_format_fixture("unsupported_integer_precision.mzml"))
    integer_validation = validate_proteomics_input(
        _format_fixture("unsupported_integer_precision.mzml"),
        input_kind=ProteomicsFormatKind.MZML,
    )

    assert len(numpress_report.accepted_spectra) == 0
    assert {issue.code for issue in numpress_report.rejected_spectra[0].issues} >= {
        "unsupported_binary_compression"
    }
    assert numpress_validation.valid is False
    assert {issue.code for issue in numpress_validation.issues} >= {
        "unsupported_binary_compression"
    }
    assert len(integer_report.accepted_spectra) == 0
    assert {issue.code for issue in integer_report.rejected_spectra[0].issues} >= {
        "unsupported_binary_precision"
    }
    assert integer_validation.valid is False
    assert {issue.code for issue in integer_validation.issues} >= {
        "unsupported_binary_precision"
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


def test_design_table_parser_preserves_cohort_and_multiplex_semantics() -> None:
    report = parse_experimental_design_table(_format_fixture("semantic.design.tsv"))

    assert len(report.accepted_entries) == 3
    assert report.accepted_entries[0].cohort == "discovery"
    assert report.accepted_entries[0].multiplex_group == "plex-a"
    assert report.accepted_entries[1].multiplex_channel == "127N"
    assert (
        report.accepted_entries[2].sample_role
        is ExperimentalDesignSampleRole.POOLED_REFERENCE
    )


def test_design_table_parser_preserves_pairing_and_extra_metadata() -> None:
    report = parse_experimental_design_table(
        _format_fixture("paired_metadata.design.tsv")
    )

    assert len(report.accepted_entries) == 2
    assert report.accepted_entries[0].pair_id == "pair-a"
    assert report.accepted_entries[0].metadata == {
        "age_years": "41",
        "sex": "female",
    }


def test_design_table_parser_rejects_partial_multiplex_semantics() -> None:
    report = parse_experimental_design_table(
        _format_fixture("invalid_multiplex.design.tsv")
    )

    assert not report.accepted_entries
    assert len(report.rejected_rows) == 1
    assert (
        "row must provide 'multiplex_group' and 'multiplex_channel' together"
        in report.rejected_rows[0].issues[0].message
    )


def test_unsupported_format_diagnostic_reports_detection_failure_reasons() -> None:
    diagnostic = diagnose_proteomics_format(_format_fixture("unsupported_vendor.raw"))

    assert diagnostic.supported is False
    assert diagnostic.detected_format is None
    assert any("'.raw'" in reason for reason in diagnostic.reasons)

    try:
        detect_proteomics_format(_format_fixture("unsupported_vendor.raw"))
    except ValueError as exc:
        assert "unsupported proteomics format" in str(exc)
        assert ".raw" in str(exc)
    else:
        raise AssertionError("expected unsupported format detection failure")


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


def test_repeated_mzml_to_mgf_conversion_produces_stable_output(tmp_path: Path) -> None:
    first_output = tmp_path / "first.mgf"
    second_output = tmp_path / "second.mgf"

    convert_proteomics_format(
        input_path=_format_fixture("simple.mzml"),
        output_path=first_output,
        input_kind=ProteomicsFormatKind.MZML,
        target_format=FormatConversionTarget.MGF,
    )
    convert_proteomics_format(
        input_path=_format_fixture("simple.mzml"),
        output_path=second_output,
        input_kind=ProteomicsFormatKind.MZML,
        target_format=FormatConversionTarget.MGF,
    )

    assert first_output.read_text() == second_output.read_text()
