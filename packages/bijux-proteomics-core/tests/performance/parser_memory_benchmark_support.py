# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from dataclasses import dataclass
import gc
from pathlib import Path
import tracemalloc

from bijux_proteomics.benchmarks import (
    ParserMemoryBenchmarkInput,
    ParserMemoryBenchmarkReport,
    build_parser_memory_benchmark_report,
)
from bijux_proteomics.identification.diann_import import build_diann_import_report
from bijux_proteomics.identification.fragpipe_import import (
    build_fragpipe_import_report,
)
from bijux_proteomics.identification.maxquant_import import (
    build_maxquant_import_report,
)
from bijux_proteomics.io.mgf_streaming import iter_mgf_spectra
from bijux_proteomics.io.mzml_reader import stream_mzml_spectra
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.targeted.target_matrix import (
    build_transition_table_targeted_matrix_report,
)


@dataclass(frozen=True)
class ParserMemoryBenchmarkCase:
    parser_id: str
    workload_unit: str
    generated_unit_count: int
    memory_ceiling_mb: float


PARSER_MEMORY_BENCHMARK_CASES: dict[str, ParserMemoryBenchmarkCase] = {
    "mgf_streaming": ParserMemoryBenchmarkCase(
        parser_id="mgf_streaming",
        workload_unit="spectra",
        generated_unit_count=8_000,
        memory_ceiling_mb=8.0,
    ),
    "mzml_streaming": ParserMemoryBenchmarkCase(
        parser_id="mzml_streaming",
        workload_unit="spectra",
        generated_unit_count=3_000,
        memory_ceiling_mb=10.0,
    ),
    "diann_import": ParserMemoryBenchmarkCase(
        parser_id="diann_import",
        workload_unit="rows",
        generated_unit_count=4_000,
        memory_ceiling_mb=80.0,
    ),
    "maxquant_import": ParserMemoryBenchmarkCase(
        parser_id="maxquant_import",
        workload_unit="rows",
        generated_unit_count=4_000,
        memory_ceiling_mb=96.0,
    ),
    "fragpipe_import": ParserMemoryBenchmarkCase(
        parser_id="fragpipe_import",
        workload_unit="rows",
        generated_unit_count=4_000,
        memory_ceiling_mb=80.0,
    ),
    "ms1_feature_table": ParserMemoryBenchmarkCase(
        parser_id="ms1_feature_table",
        workload_unit="rows",
        generated_unit_count=8_000,
        memory_ceiling_mb=24.0,
    ),
    "transition_table_matrix": ParserMemoryBenchmarkCase(
        parser_id="transition_table_matrix",
        workload_unit="rows",
        generated_unit_count=8_000,
        memory_ceiling_mb=80.0,
    ),
}


def benchmark_mgf_streaming_memory(tmp_path: Path) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["mgf_streaming"]
    path = tmp_path / "large_streaming_input.mgf"
    _write_generated_mgf(path, spectrum_count=case.generated_unit_count)
    parsed_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: sum(1 for _ in iter_mgf_spectra(path))
    )
    assert parsed_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_file_size_mb(path),
        peak_memory_mb=peak_memory_mb,
    )


def benchmark_mzml_streaming_memory(tmp_path: Path) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["mzml_streaming"]
    path = tmp_path / "large_streaming_input.mzml"
    _write_generated_mzml(path, spectrum_count=case.generated_unit_count)
    parsed_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: sum(1 for _ in stream_mzml_spectra(path))
    )
    assert parsed_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_file_size_mb(path),
        peak_memory_mb=peak_memory_mb,
    )


def benchmark_diann_import_memory(tmp_path: Path) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["diann_import"]
    bundle_dir = tmp_path / "diann"
    bundle_dir.mkdir()
    result_path = bundle_dir / "diann_report.tsv"
    config_path = bundle_dir / "diann_config.json"
    _write_generated_diann_report(
        result_path,
        row_count=case.generated_unit_count,
    )
    config_path.write_text(
        _diann_fixture("diann_config.json").read_text(encoding="utf-8")
    )

    accepted_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: (
            build_diann_import_report(
                result_path, config_path=config_path
            ).summary.accepted_precursor_count
        )
    )
    assert accepted_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_total_size_mb((result_path, config_path)),
        peak_memory_mb=peak_memory_mb,
    )


def benchmark_maxquant_import_memory(tmp_path: Path) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["maxquant_import"]
    bundle_dir = tmp_path / "maxquant"
    bundle_dir.mkdir()
    paths = _write_generated_maxquant_bundle(
        bundle_dir,
        row_count=case.generated_unit_count,
    )
    accepted_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: (
            build_maxquant_import_report(
                paths["evidence"],
                peptides_txt_path=paths["peptides"],
                protein_groups_txt_path=paths["protein_groups"],
                config_path=paths["config"],
            ).summary.accepted_evidence_count
        )
    )
    assert accepted_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_total_size_mb(tuple(paths.values())),
        peak_memory_mb=peak_memory_mb,
    )


def benchmark_fragpipe_import_memory(tmp_path: Path) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["fragpipe_import"]
    bundle_dir = tmp_path / "fragpipe"
    bundle_dir.mkdir()
    paths = _write_generated_fragpipe_bundle(
        bundle_dir,
        row_count=case.generated_unit_count,
    )
    accepted_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: (
            build_fragpipe_import_report(
                paths["psm"],
                peptide_tsv_path=paths["peptide"],
                protein_tsv_path=paths["protein"],
                quant_tsv_path=paths["quant"],
            ).summary.accepted_psm_count
        )
    )
    assert accepted_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_total_size_mb(tuple(paths.values())),
        peak_memory_mb=peak_memory_mb,
    )


def benchmark_ms1_feature_table_memory(tmp_path: Path) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["ms1_feature_table"]
    path = tmp_path / "large_ms1_features.tsv"
    _write_generated_ms1_feature_table(path, row_count=case.generated_unit_count)
    accepted_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: parse_ms1_feature_table(path).total_rows
    )
    assert accepted_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_file_size_mb(path),
        peak_memory_mb=peak_memory_mb,
    )


def benchmark_transition_table_matrix_memory(
    tmp_path: Path,
) -> ParserMemoryBenchmarkReport:
    case = PARSER_MEMORY_BENCHMARK_CASES["transition_table_matrix"]
    path = tmp_path / "large_transition_table.tsv"
    _write_generated_transition_table(path, row_count=case.generated_unit_count)
    retained_count, peak_memory_mb = _measure_peak_memory_mb(
        lambda: (
            build_transition_table_targeted_matrix_report(
                path
            ).summary.retained_transition_count
        )
    )
    assert retained_count == case.generated_unit_count
    return _build_report(
        case,
        input_size_mb=_file_size_mb(path),
        peak_memory_mb=peak_memory_mb,
    )


def _build_report(
    case: ParserMemoryBenchmarkCase,
    *,
    input_size_mb: float,
    peak_memory_mb: float,
) -> ParserMemoryBenchmarkReport:
    return build_parser_memory_benchmark_report(
        ParserMemoryBenchmarkInput(
            parser_id=case.parser_id,
            workload_unit=case.workload_unit,
            generated_unit_count=case.generated_unit_count,
            input_size_mb=input_size_mb,
            peak_memory_mb=peak_memory_mb,
            memory_ceiling_mb=case.memory_ceiling_mb,
        )
    )


def _measure_peak_memory_mb(callback):
    gc.collect()
    tracemalloc.start()
    try:
        result = callback()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        gc.collect()
    return result, peak / (1024.0 * 1024.0)


def _write_generated_mgf(path: Path, *, spectrum_count: int) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for index in range(1, spectrum_count + 1):
            handle.write("BEGIN IONS\n")
            handle.write(f"SCANS=scan={index}\n")
            handle.write(f"TITLE=streamed spectrum {index}\n")
            handle.write(f"PEPMASS={400.0 + index / 1000.0:.4f}\n")
            handle.write("CHARGE=2+\n")
            handle.write(f"RTINSECONDS={10.0 + index:.2f}\n")
            handle.write("100.0 10.0\n")
            handle.write("200.0 20.0\n")
            handle.write("END IONS\n")


def _write_generated_mzml(path: Path, *, spectrum_count: int) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        handle.write('<mzML xmlns="http://psi.hupo.org/ms/mzml" version="1.1.0">\n')
        handle.write('  <cvList count="1">\n')
        handle.write(
            '    <cv id="MS" fullName="Proteomics Standards Initiative Mass Spectrometry Ontology" version="4.1.0" URI="https://example.org/ms.obo" />\n'
        )
        handle.write("  </cvList>\n")
        handle.write('  <instrumentConfigurationList count="1">\n')
        handle.write('    <instrumentConfiguration id="IC1">\n')
        handle.write('      <cvParam accession="MS:1001911" name="Q Exactive" />\n')
        handle.write("    </instrumentConfiguration>\n")
        handle.write("  </instrumentConfigurationList>\n")
        handle.write(
            '  <run id="RUN_001" defaultInstrumentConfigurationRef="IC1" startTimeStamp="2026-04-29T10:00:00Z">\n'
        )
        handle.write(f'    <spectrumList count="{spectrum_count}">\n')
        for index in range(spectrum_count):
            scan_number = 5_001 + index
            previous_scan = scan_number - 1
            rt_seconds = 123.4 + float(index)
            precursor_mz = 500.2 + (index % 17) * 0.1
            charge = 2 + (index % 2)
            handle.write(
                f'      <spectrum id="scan={scan_number}" index="{index}" defaultArrayLength="4">\n'
            )
            handle.write(
                '        <cvParam accession="MS:1000511" name="ms level" value="2" />\n'
            )
            handle.write('        <scanList count="1">\n')
            handle.write("          <scan>\n")
            handle.write(
                f'            <cvParam accession="MS:1000016" name="scan start time" value="{rt_seconds:.1f}" unitName="second" />\n'
            )
            handle.write("          </scan>\n")
            handle.write("        </scanList>\n")
            handle.write('        <precursorList count="1">\n')
            handle.write(f'          <precursor spectrumRef="scan={previous_scan}">\n')
            handle.write('            <selectedIonList count="1">\n')
            handle.write("              <selectedIon>\n")
            handle.write(
                f'                <cvParam accession="MS:1000744" name="selected ion m/z" value="{precursor_mz:.1f}" />\n'
            )
            handle.write(
                f'                <cvParam accession="MS:1000041" name="charge state" value="{charge}" />\n'
            )
            handle.write("              </selectedIon>\n")
            handle.write("            </selectedIonList>\n")
            handle.write("          </precursor>\n")
            handle.write("        </precursorList>\n")
            handle.write('        <binaryDataArrayList count="2">\n')
            handle.write('          <binaryDataArray encodedLength="44">\n')
            handle.write(
                '            <cvParam accession="MS:1000514" name="m/z array" />\n'
            )
            handle.write(
                '            <cvParam accession="MS:1000523" name="64-bit float" />\n'
            )
            handle.write(
                '            <cvParam accession="MS:1000576" name="no compression" />\n'
            )
            handle.write(
                "            <binary>AAAAAAAAWUAAAAAAAMBiQAQ3UrZIY2xA8nowKb6Cd0A=</binary>\n"
            )
            handle.write("          </binaryDataArray>\n")
            handle.write('          <binaryDataArray encodedLength="44">\n')
            handle.write(
                '            <cvParam accession="MS:1000515" name="intensity array" />\n'
            )
            handle.write(
                '            <cvParam accession="MS:1000523" name="64-bit float" />\n'
            )
            handle.write(
                '            <cvParam accession="MS:1000576" name="no compression" />\n'
            )
            handle.write(
                "            <binary>AAAAAAAANEAAAAAAAIBGQAAAAAAAQFVAAAAAAAAAWUA=</binary>\n"
            )
            handle.write("          </binaryDataArray>\n")
            handle.write("        </binaryDataArrayList>\n")
            handle.write("      </spectrum>\n")
        handle.write("    </spectrumList>\n")
        handle.write("  </run>\n")
        handle.write("</mzML>\n")


def _write_generated_diann_report(path: Path, *, row_count: int) -> None:
    rows = _load_delimited_rows(_diann_fixture("diann_report.tsv"))
    _write_delimited_rows(
        path,
        fieldnames=tuple(rows[0].keys()),
        rows=(
            {
                **rows[index % len(rows)],
                "Precursor.Id": f"{rows[index % len(rows)]['Precursor.Id']}_{index}",
                "Protein.Group": f"{rows[index % len(rows)]['Protein.Group']}_{index}",
            }
            for index in range(row_count)
        ),
    )


def _write_generated_maxquant_bundle(
    bundle_dir: Path,
    *,
    row_count: int,
) -> dict[str, Path]:
    evidence_path = bundle_dir / "evidence.txt"
    peptides_path = bundle_dir / "peptides.txt"
    protein_groups_path = bundle_dir / "proteinGroups.txt"
    config_path = bundle_dir / "maxquant_settings.txt"
    evidence_rows = _load_delimited_rows(_maxquant_fixture("evidence.txt"))
    peptide_rows = _load_delimited_rows(_maxquant_fixture("peptides.txt"))
    protein_group_rows = _load_delimited_rows(_maxquant_fixture("proteinGroups.txt"))
    _write_delimited_rows(
        evidence_path,
        fieldnames=tuple(evidence_rows[0].keys()),
        rows=(
            _mutate_maxquant_evidence_row(
                evidence_rows[index % len(evidence_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    _write_delimited_rows(
        peptides_path,
        fieldnames=tuple(peptide_rows[0].keys()),
        rows=(
            _mutate_maxquant_peptide_row(
                peptide_rows[index % len(peptide_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    _write_delimited_rows(
        protein_groups_path,
        fieldnames=tuple(protein_group_rows[0].keys()),
        rows=(
            _mutate_maxquant_protein_group_row(
                protein_group_rows[index % len(protein_group_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    config_path.write_text(
        _maxquant_fixture("maxquant_settings.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return {
        "evidence": evidence_path,
        "peptides": peptides_path,
        "protein_groups": protein_groups_path,
        "config": config_path,
    }


def _write_generated_fragpipe_bundle(
    bundle_dir: Path,
    *,
    row_count: int,
) -> dict[str, Path]:
    psm_path = bundle_dir / "psm.tsv"
    peptide_path = bundle_dir / "combined_peptide.tsv"
    protein_path = bundle_dir / "combined_protein.tsv"
    quant_path = bundle_dir / "combined_quant.tsv"
    psm_rows = _load_delimited_rows(_fragpipe_fixture("psm.tsv"))
    peptide_rows = _load_delimited_rows(_fragpipe_fixture("combined_peptide.tsv"))
    protein_rows = _load_delimited_rows(_fragpipe_fixture("combined_protein.tsv"))
    quant_rows = _load_delimited_rows(_fragpipe_fixture("combined_quant.tsv"))
    _write_delimited_rows(
        psm_path,
        fieldnames=tuple(psm_rows[0].keys()),
        rows=(
            _mutate_fragpipe_psm_row(
                psm_rows[index % len(psm_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    _write_delimited_rows(
        peptide_path,
        fieldnames=tuple(peptide_rows[0].keys()),
        rows=(
            _mutate_fragpipe_peptide_row(
                peptide_rows[index % len(peptide_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    _write_delimited_rows(
        protein_path,
        fieldnames=tuple(protein_rows[0].keys()),
        rows=(
            _mutate_fragpipe_protein_row(
                protein_rows[index % len(protein_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    _write_delimited_rows(
        quant_path,
        fieldnames=tuple(quant_rows[0].keys()),
        rows=(
            _mutate_fragpipe_quant_row(
                quant_rows[index % len(quant_rows)],
                index=index,
            )
            for index in range(row_count)
        ),
    )
    return {
        "psm": psm_path,
        "peptide": peptide_path,
        "protein": protein_path,
        "quant": quant_path,
    }


def _write_generated_ms1_feature_table(path: Path, *, row_count: int) -> None:
    rows = _load_delimited_rows(_quant_fixture("ms1_features.tsv"))
    _write_delimited_rows(
        path,
        fieldnames=tuple(rows[0].keys()),
        rows=(
            {
                **rows[index % len(rows)],
                "feature_id": f"{rows[index % len(rows)]['feature_id']}_{index}",
            }
            for index in range(row_count)
        ),
    )


def _write_generated_transition_table(path: Path, *, row_count: int) -> None:
    rows = _load_delimited_rows(_format_fixture("transition_quant.tsv"))
    _write_delimited_rows(
        path,
        fieldnames=tuple(rows[0].keys()),
        rows=(
            {
                **rows[index % len(rows)],
                "transition_id": f"{rows[index % len(rows)]['transition_id']}_{index}",
                "precursor_id": (
                    f"{rows[index % len(rows)]['precursor_id']}_{index // 2}"
                ),
            }
            for index in range(row_count)
        ),
    )


def _load_delimited_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8").splitlines()
    delimiter = "\t" if text and "\t" in text[0] else ","
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def _mutate_maxquant_evidence_row(row: dict[str, str], *, index: int) -> dict[str, str]:
    peptide_suffix = _amino_suffix(index)
    id_suffix = _id_suffix(index)
    return {
        **row,
        "MS/MS scan number": str(100_000 + index),
        "Sequence": row["Sequence"] + peptide_suffix,
        "Modified sequence": _append_maxquant_peptide_suffix(
            row["Modified sequence"],
            peptide_suffix,
        ),
        "Proteins": _suffix_delimited_tokens(row["Proteins"], id_suffix),
    }


def _mutate_maxquant_peptide_row(row: dict[str, str], *, index: int) -> dict[str, str]:
    peptide_suffix = _amino_suffix(index)
    id_suffix = _id_suffix(index)
    return {
        **row,
        "Sequence": row["Sequence"] + peptide_suffix,
        "Modified sequence": _append_maxquant_peptide_suffix(
            row["Modified sequence"],
            peptide_suffix,
        ),
        "Proteins": _suffix_delimited_tokens(row["Proteins"], id_suffix),
        "Leading razor protein": row["Leading razor protein"] + id_suffix,
    }


def _mutate_maxquant_protein_group_row(
    row: dict[str, str],
    *,
    index: int,
) -> dict[str, str]:
    id_suffix = _id_suffix(index)
    return {
        **row,
        "Protein IDs": _suffix_delimited_tokens(row["Protein IDs"], id_suffix),
        "Majority protein IDs": _suffix_delimited_tokens(
            row["Majority protein IDs"],
            id_suffix,
        ),
        "Gene names": _suffix_delimited_tokens(row["Gene names"], id_suffix),
    }


def _mutate_fragpipe_psm_row(row: dict[str, str], *, index: int) -> dict[str, str]:
    peptide_suffix = _amino_suffix(index)
    id_suffix = _id_suffix(index)
    return {
        **row,
        "Spectrum": f"{row['Spectrum']}_{index}",
        "Peptide": row["Peptide"] + peptide_suffix,
        "Modified Peptide": row["Modified Peptide"] + peptide_suffix,
        "Protein": row["Protein"] + id_suffix,
    }


def _mutate_fragpipe_peptide_row(row: dict[str, str], *, index: int) -> dict[str, str]:
    peptide_suffix = _amino_suffix(index)
    id_suffix = _id_suffix(index)
    return {
        **row,
        "Peptide": row["Peptide"] + peptide_suffix,
        "Modified Peptide": row["Modified Peptide"] + peptide_suffix,
        "Protein": row["Protein"] + id_suffix,
        "Mapped Proteins": _suffix_delimited_tokens(
            row["Mapped Proteins"],
            id_suffix,
        ),
    }


def _mutate_fragpipe_protein_row(row: dict[str, str], *, index: int) -> dict[str, str]:
    id_suffix = _id_suffix(index)
    return {
        **row,
        "Protein": row["Protein"] + id_suffix,
        "Entry Name": row["Entry Name"] + id_suffix,
        "Gene": row["Gene"] + id_suffix if row["Gene"] else row["Gene"],
    }


def _mutate_fragpipe_quant_row(row: dict[str, str], *, index: int) -> dict[str, str]:
    return {
        **row,
        "Protein": row["Protein"] + _id_suffix(index),
    }


def _write_delimited_rows(
    path: Path,
    *,
    fieldnames: tuple[str, ...],
    rows,
) -> None:
    delimiter = "\t" if path.suffix in {".tsv", ".txt"} else ","
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def _file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024.0 * 1024.0)


def _total_size_mb(paths: tuple[Path, ...]) -> float:
    return sum(path.stat().st_size for path in paths) / (1024.0 * 1024.0)


def _fixture_root() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures"


def _diann_fixture(name: str) -> Path:
    return _fixture_root() / "search_result_bundles" / "diann" / name


def _maxquant_fixture(name: str) -> Path:
    return _fixture_root() / "search_result_bundles" / "maxquant" / name


def _fragpipe_fixture(name: str) -> Path:
    return _fixture_root() / "search_result_bundles" / "fragpipe" / name


def _quant_fixture(name: str) -> Path:
    return _fixture_root() / "quant" / name


def _format_fixture(name: str) -> Path:
    return _fixture_root() / "formats" / name


def _append_maxquant_peptide_suffix(peptide: str, suffix: str) -> str:
    if peptide.startswith("_") and peptide.endswith("_"):
        return peptide[:-1] + suffix + "_"
    return peptide + suffix


def _suffix_delimited_tokens(value: str, suffix: str) -> str:
    if not value:
        return value
    return ";".join(f"{token}{suffix}" for token in value.split(";"))


def _id_suffix(index: int) -> str:
    return f"_mem{index}"


def _amino_suffix(index: int) -> str:
    alphabet = "ACDEFGHIKLMNPQRSTVWY"
    value = index + 1
    characters: list[str] = []
    while value > 0:
        value, remainder = divmod(value - 1, len(alphabet))
        characters.append(alphabet[remainder])
    return "".join(reversed(characters))
