# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import base64
import csv
from pathlib import Path
import struct

from bijux_proteomics.io.formats import parse_mzml
from bijux_proteomics.io.spectra import parse_mgf
from bijux_proteomics_runtime.streaming import (
    StreamingImportFormat,
    StreamingImportRecord,
    StreamingImportStep,
    iter_streaming_import_batches,
    run_streaming_import_step,
)

_MEMORY_LIMIT_BYTES = 12 * 1024 * 1024
_SUBSET_LIMIT = 25


def _spectrum_record_from_eager(
    *,
    spectrum_id: str,
    native_id: str | None,
    scan_number: int | None,
    ms_level: int | None,
    precursor_mz: float,
    precursor_charge: int | None,
    retention_time_seconds: float | None,
    peak_count: int,
) -> StreamingImportRecord:
    return StreamingImportRecord(
        record_id=spectrum_id,
        fields={
            "native_id": native_id,
            "scan_number": scan_number,
            "ms_level": ms_level,
            "precursor_mz": precursor_mz,
            "precursor_charge": precursor_charge,
            "retention_time_seconds": retention_time_seconds,
            "peak_count": peak_count,
        },
    )


def _expected_mgf_subset(path: Path) -> tuple[StreamingImportRecord, ...]:
    report = parse_mgf(path)
    return tuple(
        _spectrum_record_from_eager(
            spectrum_id=spectrum.spectrum_id,
            native_id=spectrum.native_id,
            scan_number=spectrum.scan_number,
            ms_level=spectrum.ms_level,
            precursor_mz=spectrum.precursor_mz,
            precursor_charge=spectrum.precursor_charge,
            retention_time_seconds=spectrum.retention_time_seconds,
            peak_count=len(spectrum.peaks),
        )
        for spectrum in report.accepted_spectra[:_SUBSET_LIMIT]
    )


def _expected_mzml_subset(path: Path) -> tuple[StreamingImportRecord, ...]:
    report = parse_mzml(path)
    return tuple(
        _spectrum_record_from_eager(
            spectrum_id=spectrum.spectrum_id,
            native_id=spectrum.native_id,
            scan_number=spectrum.scan_number,
            ms_level=spectrum.ms_level,
            precursor_mz=spectrum.precursor_mz,
            precursor_charge=spectrum.precursor_charge,
            retention_time_seconds=spectrum.retention_time_seconds,
            peak_count=len(spectrum.peaks),
        )
        for spectrum in report.accepted_spectra[:_SUBSET_LIMIT]
    )


def _expected_tsv_subset(path: Path) -> tuple[StreamingImportRecord, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)[:_SUBSET_LIMIT]
    return tuple(
        StreamingImportRecord(
            record_id=row["record_id"],
            fields={
                "record_id": row["record_id"],
                "peptide": row["peptide"],
                "intensity": row["intensity"],
            },
        )
        for row in rows
    )


def _write_large_mgf(path: Path, *, spectrum_count: int) -> None:
    lines: list[str] = []
    for index in range(1, spectrum_count + 1):
        lines.extend(
            (
                "BEGIN IONS",
                f"TITLE=scan={index}",
                f"SCANS={index}",
                f"PEPMASS={500.0 + index / 1000:.4f} 1000.0",
                "CHARGE=2+",
                f"RTINSECONDS={float(index):.2f}",
                f"{100.0 + index / 1000:.4f} 250.0",
                f"{150.0 + index / 1000:.4f} 400.0",
                "END IONS",
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _encode_float64(values: tuple[float, ...]) -> str:
    payload = struct.pack("<" + ("d" * len(values)), *values)
    return base64.b64encode(payload).decode("ascii")


def _write_large_mzml(path: Path, *, spectrum_count: int) -> None:
    spectra: list[str] = []
    for index in range(1, spectrum_count + 1):
        mz_values = (100.0 + index / 1000.0, 150.0 + index / 1000.0)
        intensity_values = (250.0 + index, 500.0 + index)
        spectra.append(
            f"""
      <spectrum id="scan={index}" index="{index - 1}" defaultArrayLength="2">
        <cvParam accession="MS:1000511" value="2" />
        <scanList count="1">
          <scan>
            <cvParam accession="MS:1000016" value="{index / 10:.2f}" unitName="minute" />
          </scan>
        </scanList>
        <precursorList count="1">
          <precursor spectrumRef="scan={max(index - 1, 1)}">
            <selectedIonList count="1">
              <selectedIon>
                <cvParam accession="MS:1000744" value="{500.0 + index / 1000:.4f}" />
                <cvParam accession="MS:1000041" value="2" />
                <cvParam accession="MS:1000042" value="{1000.0 + index:.1f}" />
              </selectedIon>
            </selectedIonList>
          </precursor>
        </precursorList>
        <binaryDataArrayList count="2">
          <binaryDataArray encodedLength="0">
            <cvParam accession="MS:1000514" />
            <cvParam accession="MS:1000523" />
            <cvParam accession="MS:1000576" />
            <binary>{_encode_float64(mz_values)}</binary>
          </binaryDataArray>
          <binaryDataArray encodedLength="0">
            <cvParam accession="MS:1000515" />
            <cvParam accession="MS:1000523" />
            <cvParam accession="MS:1000576" />
            <binary>{_encode_float64(intensity_values)}</binary>
          </binaryDataArray>
        </binaryDataArrayList>
      </spectrum>""".strip()
        )
    payload = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mzML xmlns="http://psi.hupo.org/ms/mzml">\n'
        '  <run id="streaming-run">\n'
        f'    <spectrumList count="{spectrum_count}">\n'
        + "\n".join(spectra)
        + "\n    </spectrumList>\n"
        "  </run>\n"
        "</mzML>\n"
    )
    path.write_text(payload, encoding="utf-8")


def _write_large_tsv(path: Path, *, row_count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("record_id", "peptide", "intensity"))
        for index in range(1, row_count + 1):
            writer.writerow((f"row-{index}", f"PEPTIDE{index}", f"{1000 + index}.0"))


def test_run_streaming_import_step_keeps_large_inputs_under_fixed_memory_and_matches_eager_subsets(
    tmp_path: Path,
) -> None:
    mgf_path = tmp_path / "artifacts" / "large.mgf"
    mzml_path = tmp_path / "artifacts" / "large.mzML"
    tsv_path = tmp_path / "artifacts" / "large.tsv"
    mgf_path.parent.mkdir(parents=True)
    _write_large_mgf(mgf_path, spectrum_count=1800)
    _write_large_mzml(mzml_path, spectrum_count=900)
    _write_large_tsv(tsv_path, row_count=6000)

    mgf_report = run_streaming_import_step(
        StreamingImportStep(
            step_id="import-mgf",
            path=str(mgf_path),
            format=StreamingImportFormat.MGF,
            batch_size=64,
            memory_limit_bytes=_MEMORY_LIMIT_BYTES,
        ),
        subset_limit=_SUBSET_LIMIT,
    )
    mzml_report = run_streaming_import_step(
        StreamingImportStep(
            step_id="import-mzml",
            path=str(mzml_path),
            format=StreamingImportFormat.MZML,
            batch_size=48,
            memory_limit_bytes=_MEMORY_LIMIT_BYTES,
        ),
        subset_limit=_SUBSET_LIMIT,
    )
    tsv_report = run_streaming_import_step(
        StreamingImportStep(
            step_id="import-tsv",
            path=str(tsv_path),
            format=StreamingImportFormat.TSV,
            batch_size=128,
            memory_limit_bytes=_MEMORY_LIMIT_BYTES,
            id_column="record_id",
            selected_columns=("record_id", "peptide", "intensity"),
        ),
        subset_limit=_SUBSET_LIMIT,
    )

    assert mgf_report.total_records == 1800
    assert mgf_report.subset_records == _expected_mgf_subset(mgf_path)
    assert mgf_report.peak_memory_bytes <= _MEMORY_LIMIT_BYTES

    assert mzml_report.total_records == 900
    assert mzml_report.subset_records == _expected_mzml_subset(mzml_path)
    assert mzml_report.peak_memory_bytes <= _MEMORY_LIMIT_BYTES

    assert tsv_report.total_records == 6000
    assert tsv_report.subset_records == _expected_tsv_subset(tsv_path)
    assert tsv_report.peak_memory_bytes <= _MEMORY_LIMIT_BYTES


def test_iter_streaming_import_batches_preserves_bounded_batch_windows_for_large_tsv_inputs(
    tmp_path: Path,
) -> None:
    tsv_path = tmp_path / "artifacts" / "chunked.tsv"
    tsv_path.parent.mkdir(parents=True)
    _write_large_tsv(tsv_path, row_count=205)

    batches = tuple(
        iter_streaming_import_batches(
            StreamingImportStep(
                step_id="chunked-tsv-import",
                path=str(tsv_path),
                format=StreamingImportFormat.TSV,
                batch_size=32,
                memory_limit_bytes=_MEMORY_LIMIT_BYTES,
                id_column="record_id",
                selected_columns=("record_id", "peptide"),
            )
        )
    )

    assert [batch.record_count for batch in batches] == [32, 32, 32, 32, 32, 32, 13]
    assert all(batch.record_count <= 32 for batch in batches)
    assert batches[0].records[0].record_id == "row-1"
    assert batches[-1].records[-1].record_id == "row-205"
