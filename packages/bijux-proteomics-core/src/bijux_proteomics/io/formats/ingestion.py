# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced ingestion boundaries for proteomics exchange formats."""

from __future__ import annotations

from collections.abc import Iterator
import csv
from enum import StrEnum
from pathlib import Path

from defusedxml import ElementTree as ET
from pydantic import ConfigDict, Field

from bijux_proteomics.io.raw.mgf_streaming import (
    count_mgf_blocks,
    iter_mgf_spectra,
)
from bijux_proteomics.io.raw.mzml_reader import (
    build_mzml_practical_review_report as _build_mzml_practical_review_report,
    inspect_mzml_decoding_support as _inspect_mzml_decoding_support,
    stream_mzml_spectra,
)
from bijux_proteomics.io.spectra import SpectrumModel
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    parse_ms1_feature_table,
)
from bijux_proteomics_foundation import JsonModel


class MzIdentMlIngestionReport(JsonModel):
    """Structured mzIdentML ingestion support/refusal report."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    spectrum_identification_result_count: int = Field(..., ge=0)
    spectrum_identification_item_count: int = Field(..., ge=0)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)
    lost_fields: tuple[str, ...] = Field(default_factory=tuple)


class MzTabIngestionReport(JsonModel):
    """Structured mzTab-M/mzTab-P ingestion support and field coverage report."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    variant: str | None = None
    row_counts: dict[str, int] = Field(default_factory=dict)
    mapped_fields: tuple[str, ...] = Field(default_factory=tuple)
    lost_fields: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_fields: tuple[str, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class XmlIdentificationBoundaryReport(JsonModel):
    """Boundary report for pepXML/idXML identification XML formats."""

    model_config = ConfigDict(extra="forbid")

    detected_format: str | None = None
    supported: bool
    required_conversion: str | None = None
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)
    record_count: int = Field(default=0, ge=0)


class ChromatogramQcPoint(JsonModel):
    """One chromatogram QC data point with TIC/BPC support."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    scan_time_seconds: float = Field(..., ge=0.0)
    tic: float | None = Field(default=None, ge=0.0)
    bpc: float | None = Field(default=None, ge=0.0)


class ChromatogramQcIngestionReport(JsonModel):
    """Chromatogram QC ingestion report with unknown-vs-failed metric clarity."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_points: tuple[ChromatogramQcPoint, ...] = Field(default_factory=tuple)
    unknown_metric_rows: int = Field(..., ge=0)
    failed_metric_rows: int = Field(..., ge=0)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class Ms1FeatureTableIngestionReport(JsonModel):
    """MS1 feature ingestion report with units and provenance field coverage."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    observed_charge_rows: int = Field(..., ge=0)
    observed_mz_rows: int = Field(..., ge=0)
    observed_retention_time_rows: int = Field(..., ge=0)
    units: dict[str, str] = Field(default_factory=dict)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class SpectrumLibraryBoundaryReport(JsonModel):
    """Boundary report for spectral-library format support/refusal."""

    model_config = ConfigDict(extra="forbid")

    format_name: str
    supported: bool
    support_mode: str | None = None
    entry_count: int = Field(default=0, ge=0)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)
    mapped_fields: tuple[str, ...] = Field(default_factory=tuple)


class IonMobilityObservation(JsonModel):
    """One ion-mobility observation extracted from mzML scan metadata."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    value: float
    unit_name: str | None = None


class IonMobilitySupportReport(JsonModel):
    """Ion mobility support report for mzML ingestion surfaces."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    total_spectra: int = Field(..., ge=0)
    observed_count: int = Field(..., ge=0)
    observations: tuple[IonMobilityObservation, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class StreamingParseProfile(JsonModel):
    """Streaming parse profile over large MGF/mzML inputs."""

    model_config = ConfigDict(extra="forbid")

    format_name: str
    chunk_size: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=0)
    chunk_count: int = Field(..., ge=0)
    first_spectrum_id: str | None = None
    last_spectrum_id: str | None = None
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class FormatCapabilityEntry(JsonModel):
    """Capability classification for one observed fixture format."""

    model_config = ConfigDict(extra="forbid")

    format_name: str
    state: str
    fixture_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class FormatCapabilityMatrixReport(JsonModel):
    """Generated capability matrix over fixture-derived format surfaces."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[FormatCapabilityEntry, ...] = Field(default_factory=tuple)
    generated_from: str = Field(..., min_length=1)


class RawSpectraDialectRealityState(StrEnum):
    """Practical support state for one raw-spectra dialect surface."""

    SUPPORTED = "supported"
    PARTIAL = "partial"
    REFUSED = "refused"


class RawSpectraDialectRealityEntry(JsonModel):
    """Reality check entry for one mzML or related raw-spectra dialect."""

    model_config = ConfigDict(extra="forbid")

    input_name: str = Field(..., min_length=1)
    format_name: str = Field(..., min_length=1)
    support_state: RawSpectraDialectRealityState
    practical_scope: str = Field(..., min_length=1)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class RawSpectraDialectRealityReport(JsonModel):
    """Practical support report over mzML, MGF, and vendor-native raw surfaces."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[RawSpectraDialectRealityEntry, ...] = Field(default_factory=tuple)
    supported_count: int = Field(..., ge=0)
    partial_count: int = Field(..., ge=0)
    refused_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def parse_mzidentml_or_refuse(path: Path) -> MzIdentMlIngestionReport:
    """Parse mzIdentML core identification surfaces or return precise refusal details."""
    root = ET.parse(path).getroot()
    if root is None:
        raise ValueError("invalid XML: missing document root")
    tag = _local_name(root.tag)
    if tag != "MzIdentML":
        return MzIdentMlIngestionReport(
            supported=False,
            spectrum_identification_result_count=0,
            spectrum_identification_item_count=0,
            diagnostics=(
                "input root is not MzIdentML",
                "supported root tag: MzIdentML",
            ),
        )

    results = root.findall(".//{*}SpectrumIdentificationResult")
    items = root.findall(".//{*}SpectrumIdentificationItem")
    if not results:
        return MzIdentMlIngestionReport(
            supported=False,
            spectrum_identification_result_count=0,
            spectrum_identification_item_count=0,
            diagnostics=(
                "missing SpectrumIdentificationResult entries",
                "file cannot be normalized into core PSM contracts without identification results",
            ),
        )

    lost_fields: list[str] = []
    if root.find(".//{*}ProteinDetectionList") is None:
        lost_fields.append("protein_detection_list")
    if root.find(".//{*}FragmentationTable") is None:
        lost_fields.append("fragmentation_table")

    return MzIdentMlIngestionReport(
        supported=True,
        spectrum_identification_result_count=len(results),
        spectrum_identification_item_count=len(items),
        diagnostics=(
            "parsed mzIdentML identification results",
            "normalization keeps explicit counts for result and item surfaces",
        ),
        lost_fields=tuple(lost_fields),
    )


def parse_mztab_or_refuse(path: Path) -> MzTabIngestionReport:
    """Parse mzTab-M/mzTab-P style rows or return explicit unsupported diagnostics."""
    rows = path.read_text(encoding="utf-8").splitlines()
    if not rows:
        return MzTabIngestionReport(
            supported=False,
            diagnostics=("mzTab input is empty",),
        )

    row_counts: dict[str, int] = {}
    headers_by_prefix: dict[str, tuple[str, ...]] = {}
    metadata: dict[str, str] = {}
    for raw in rows:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = next(csv.reader([line], delimiter="\t"))
        prefix = parts[0].strip()
        row_counts[prefix] = row_counts.get(prefix, 0) + 1
        if prefix.endswith("H"):
            headers_by_prefix[prefix] = tuple(parts[1:])
        if prefix == "MTD" and len(parts) >= 3:
            metadata[parts[1]] = parts[2]

    variant = metadata.get("mzTab-mode")
    if variant is None:
        variant = "P" if "PRT" in row_counts or "PEP" in row_counts else "M"
    if "PSM" not in row_counts and "PEP" not in row_counts and "PRT" not in row_counts:
        return MzTabIngestionReport(
            supported=False,
            variant=variant,
            row_counts=row_counts,
            diagnostics=(
                "mzTab lacks PSM/PEP/PRT data sections required for proteomics normalization",
            ),
        )

    mapped = {
        "sequence",
        "accession",
        "charge",
        "exp_mass_to_charge",
        "search_engine_score[1]",
    }
    observed_headers = {
        field for fields in headers_by_prefix.values() for field in fields
    }
    unsupported = {
        field
        for field in observed_headers
        if field.startswith(("opt_global_", "opt_assay["))
    }
    lost = sorted(
        field
        for field in ("retention_time", "calc_mass_to_charge")
        if field not in observed_headers
    )
    return MzTabIngestionReport(
        supported=True,
        variant=variant,
        row_counts=row_counts,
        mapped_fields=tuple(sorted(mapped.intersection(observed_headers))),
        lost_fields=tuple(lost),
        unsupported_fields=tuple(sorted(unsupported)),
        diagnostics=(
            "parsed mzTab table sections and preserved section row counts",
            "reported optional fields outside current normalized schema mapping",
        ),
    )


def evaluate_pepxml_idxml_boundary(path: Path) -> XmlIdentificationBoundaryReport:
    """Detect pepXML/idXML roots and return explicit conversion/support boundaries."""
    root = ET.parse(path).getroot()
    if root is None:
        raise ValueError("invalid XML: missing document root")
    tag = _local_name(root.tag)
    if tag == "msms_pipeline_analysis":
        count = len(root.findall(".//{*}spectrum_query"))
        return XmlIdentificationBoundaryReport(
            detected_format="pepXML",
            supported=False,
            required_conversion="convert pepXML to normalized PSM TSV or mzIdentML before ingestion",
            diagnostics=(
                "pepXML root detected",
                "native pepXML mapping is not yet guaranteed to preserve all score families",
            ),
            record_count=count,
        )
    if tag == "IdXML":
        count = len(root.findall(".//{*}PeptideIdentification"))
        return XmlIdentificationBoundaryReport(
            detected_format="idXML",
            supported=True,
            required_conversion=None,
            diagnostics=(
                "idXML root detected",
                "native idXML import preserves peptide and protein evidence through the owned OpenMS import surface",
            ),
            record_count=count,
        )
    return XmlIdentificationBoundaryReport(
        detected_format=tag,
        supported=False,
        required_conversion=None,
        diagnostics=("unsupported XML identification format root",),
        record_count=0,
    )


def inspect_mzml_decoding_support(path: Path):
    """Inspect mzML binary arrays and summarize decoding support boundaries."""

    return _inspect_mzml_decoding_support(path)


def build_mzml_practical_review_report(path: Path):
    """Build a practical mzML review surface without overclaiming vendor parity."""

    return _build_mzml_practical_review_report(path)


def parse_chromatogram_qc_table(path: Path) -> ChromatogramQcIngestionReport:
    """Parse TIC/BPC chromatogram QC tables and distinguish unknown from failed metrics."""
    reader = csv.DictReader(
        path.read_text(encoding="utf-8").splitlines(), delimiter="\t"
    )
    points: list[ChromatogramQcPoint] = []
    unknown_rows = 0
    failed_rows = 0
    total = 0
    for row in reader:
        total += 1
        run_id = (row.get("run_id") or "").strip()
        rt = _parse_float(row.get("scan_time_seconds"))
        tic = _parse_float(row.get("tic"))
        bpc = _parse_float(row.get("bpc"))
        if not run_id or rt is None:
            failed_rows += 1
            continue
        if tic is None and bpc is None:
            unknown_rows += 1
        points.append(
            ChromatogramQcPoint(
                run_id=run_id,
                scan_time_seconds=rt,
                tic=tic,
                bpc=bpc,
            )
        )
    return ChromatogramQcIngestionReport(
        total_rows=total,
        accepted_points=tuple(points),
        unknown_metric_rows=unknown_rows,
        failed_metric_rows=failed_rows,
        diagnostics=(
            "chromatogram QC ingestion preserves TIC/BPC values when present",
            "rows missing both TIC and BPC are tracked as unknown metrics rather than hard parse failures",
        ),
    )


def parse_ms1_feature_table_with_provenance(
    path: Path,
    *,
    mapping: Ms1FeatureColumnMapping | None = None,
) -> Ms1FeatureTableIngestionReport:
    """Parse MS1 feature tables and report units/provenance field coverage."""
    report = parse_ms1_feature_table(path, mapping=mapping)
    accepted = report.accepted_records
    return Ms1FeatureTableIngestionReport(
        total_rows=report.total_rows,
        accepted_rows=len(accepted),
        rejected_rows=len(report.rejected_rows),
        observed_charge_rows=sum(1 for row in accepted if row.charge is not None),
        observed_mz_rows=sum(1 for row in accepted if row.mz is not None),
        observed_retention_time_rows=sum(
            1 for row in accepted if row.retention_time_seconds is not None
        ),
        units={
            "retention_time_seconds": "seconds",
            "mz": "mz",
            "intensity": "instrument_intensity_units",
        },
        diagnostics=(
            "MS1 feature ingestion preserves sample/peptide/intensity required fields",
            "optional charge, m/z, and retention-time provenance are counted explicitly",
        ),
    )


def evaluate_spectrum_library_boundary(path: Path) -> SpectrumLibraryBoundaryReport:
    """Detect spectrum-library format boundaries and support/refusal modes."""
    suffix = path.suffix.lower()
    if suffix == ".msp":
        return SpectrumLibraryBoundaryReport(
            format_name="MSP",
            supported=True,
            support_mode="importable",
            entry_count=path.read_text(encoding="utf-8").count("\nName:")
            + int(path.read_text(encoding="utf-8").startswith("Name:")),
            mapped_fields=("Name", "Comment", "Num peaks", "fragment peaks"),
            diagnostics=(
                "MSP library detected with importable support mode",
                "library import preserves peptide, charge, precursor, and fragment peaks",
            ),
        )
    if suffix == ".mgf":
        return SpectrumLibraryBoundaryReport(
            format_name="MGF",
            supported=True,
            support_mode="importable",
            entry_count=count_mgf_blocks(path),
            mapped_fields=("TITLE", "PEPMASS", "CHARGE", "fragment peaks"),
            diagnostics=(
                "MGF library detected with importable support mode",
                "library import expects peptide identity in TITLE metadata",
            ),
        )
    if suffix in {".sptxt", ".traml", ".elib"}:
        return SpectrumLibraryBoundaryReport(
            format_name=suffix.lstrip("."),
            supported=False,
            support_mode=None,
            entry_count=0,
            diagnostics=(
                "library format detected but normalization support is not yet implemented",
                "convert to MSP or normalized PSM/feature exports for current ingestion workflows",
            ),
        )
    return SpectrumLibraryBoundaryReport(
        format_name=suffix.lstrip(".") or "unknown",
        supported=False,
        support_mode=None,
        entry_count=0,
        diagnostics=("unsupported spectral-library file extension",),
    )


def extract_ion_mobility_support(path: Path) -> IonMobilitySupportReport:
    """Extract ion-mobility fields from mzML and report support boundaries."""
    root = ET.parse(path).getroot()
    if root is None:
        raise ValueError("invalid XML: missing document root")
    mobility_accessions = {
        "MS:1002476",  # ion mobility drift time
        "MS:1002815",  # inverse reduced ion mobility
        "MS:1002954",  # collisional cross sectional area
    }
    observations: list[IonMobilityObservation] = []
    spectra = root.findall(".//{*}spectrum")
    for spectrum in spectra:
        spectrum_id = spectrum.attrib.get("id", "unknown")
        for param in spectrum.findall(".//{*}cvParam"):
            accession = param.attrib.get("accession", "").strip()
            if accession not in mobility_accessions:
                continue
            value = _parse_float(param.attrib.get("value"))
            if value is None:
                continue
            observations.append(
                IonMobilityObservation(
                    spectrum_id=spectrum_id,
                    accession=accession,
                    value=value,
                    unit_name=param.attrib.get("unitName"),
                )
            )
    supported = bool(observations)
    diagnostics = (
        "ion mobility fields were extracted with accession-level provenance"
        if supported
        else "no supported ion mobility cvParam entries were detected in mzML scans"
    )
    return IonMobilitySupportReport(
        supported=supported,
        total_spectra=len(spectra),
        observed_count=len(observations),
        observations=tuple(observations),
        diagnostics=(diagnostics,),
    )


def stream_mgf_spectra(path: Path) -> Iterator[SpectrumModel]:
    """Yield accepted MGF spectra one block at a time from the shared parser."""
    yield from iter_mgf_spectra(path)


def build_streaming_parse_profile(
    path: Path,
    *,
    format_name: str,
    chunk_size: int = 500,
) -> StreamingParseProfile:
    """Build a chunk-aware profile for large MGF/mzML streaming parses."""
    format_key = format_name.strip().lower()
    if format_key not in {"mgf", "mzml"}:
        raise ValueError("streaming profile currently supports only mgf and mzml")
    iterator: Iterator[SpectrumModel]
    if format_key == "mzml":
        iterator = stream_mzml_spectra(path)
    else:
        iterator = stream_mgf_spectra(path)

    spectrum_count = 0
    first_spectrum_id: str | None = None
    last_spectrum_id: str | None = None
    for spectrum in iterator:
        spectrum_count += 1
        if first_spectrum_id is None:
            first_spectrum_id = spectrum.spectrum_id
        last_spectrum_id = spectrum.spectrum_id

    chunk_count = (
        (spectrum_count + chunk_size - 1) // chunk_size if spectrum_count else 0
    )
    return StreamingParseProfile(
        format_name=format_key,
        chunk_size=chunk_size,
        spectrum_count=spectrum_count,
        chunk_count=chunk_count,
        first_spectrum_id=first_spectrum_id,
        last_spectrum_id=last_spectrum_id,
        diagnostics=(
            "streaming profile computed without relying on full-run normalization side effects",
            "chunk_count expresses bounded processing batches for larger files",
        ),
    )


def build_format_capability_matrix_from_fixtures(
    fixtures_dir: Path,
) -> FormatCapabilityMatrixReport:
    """Generate parse/write/normalized/unsupported capability states from fixtures."""
    format_files: dict[str, list[Path]] = {}
    for path in sorted(fixtures_dir.iterdir()):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in {".mzml", ".mzid", ".mztab", ".pepxml", ".idxml", ".msp", ".mgf"}:
            format_files.setdefault(suffix, []).append(path)

    entries: list[FormatCapabilityEntry] = []
    for suffix, files in sorted(format_files.items()):
        if suffix == ".mzml":
            state = "parse_and_normalize"
            note = "mzML fixtures parse to stable spectrum contracts and normalized exports"
        elif suffix == ".mgf":
            state = "parse_and_write"
            note = "MGF fixtures parse and support deterministic stream profiling"
        elif suffix == ".mzid":
            supported = any(parse_mzidentml_or_refuse(path).supported for path in files)
            state = "parse_only" if supported else "unsupported"
            note = "mzIdentML fixtures expose identification parse boundaries"
        elif suffix == ".mztab":
            supported = any(parse_mztab_or_refuse(path).supported for path in files)
            state = "parse_only" if supported else "unsupported"
            note = "mzTab fixtures expose mapped/lost/unsupported table fields"
        elif suffix in {".pepxml", ".idxml"}:
            state = "unsupported_with_conversion"
            note = "XML identification fixtures require conversion before normalized ingestion"
        elif suffix == ".msp":
            state = "parse_only"
            note = "MSP fixtures support library parse boundaries"
        else:
            state = "unsupported"
            note = "no active capability mapping"
        entries.append(
            FormatCapabilityEntry(
                format_name=suffix.lstrip("."),
                state=state,
                fixture_count=len(files),
                note=note,
            )
        )
    return FormatCapabilityMatrixReport(
        entries=tuple(entries),
        generated_from=str(fixtures_dir),
    )


def build_raw_spectra_dialect_reality_report(
    paths: tuple[Path, ...],
) -> RawSpectraDialectRealityReport:
    """Classify practical raw-spectra support without overstating vendor coverage."""

    entries: list[RawSpectraDialectRealityEntry] = []
    for path in sorted(paths, key=lambda item: item.name):
        suffix = path.suffix.lower()
        if suffix == ".mzml":
            decoding = inspect_mzml_decoding_support(path)
            support_state = (
                RawSpectraDialectRealityState.SUPPORTED
                if decoding.supported
                else RawSpectraDialectRealityState.PARTIAL
            )
            practical_scope = (
                "standard mzML float-array decoding is directly supported, but practical coverage still depends on the upstream vendor conversion path"
                if decoding.supported
                else "mzML payload is recognizable, but binary-array dialect choices still limit direct practical coverage"
            )
            entries.append(
                RawSpectraDialectRealityEntry(
                    input_name=path.name,
                    format_name="mzml",
                    support_state=support_state,
                    practical_scope=practical_scope,
                    diagnostics=decoding.diagnostics,
                )
            )
            continue
        if suffix == ".mgf":
            entries.append(
                RawSpectraDialectRealityEntry(
                    input_name=path.name,
                    format_name="mgf",
                    support_state=RawSpectraDialectRealityState.PARTIAL,
                    practical_scope=(
                        "MGF remains a parseable exchange surface, not a full instrument-native replacement for precursor and binary-array provenance"
                    ),
                    diagnostics=(
                        "MGF preserves peak lists and a bounded metadata subset",
                        "instrument-native binary encoding, chromatograms, and richer acquisition metadata remain outside the MGF scope",
                    ),
                )
            )
            continue
        if suffix in {".raw", ".wiff", ".d"}:
            entries.append(
                RawSpectraDialectRealityEntry(
                    input_name=path.name,
                    format_name=suffix.lstrip("."),
                    support_state=RawSpectraDialectRealityState.REFUSED,
                    practical_scope=(
                        "vendor-native raw files still require external conversion before current ingestion and review workflows can make scientific claims"
                    ),
                    diagnostics=(
                        "vendor-native binary dialect is not directly decoded in-repo",
                        "convert to mzML with a documented conversion path before treating the result as a supported ingestion surface",
                    ),
                )
            )
            continue
        entries.append(
            RawSpectraDialectRealityEntry(
                input_name=path.name,
                format_name=suffix.lstrip(".") or "unknown",
                support_state=RawSpectraDialectRealityState.REFUSED,
                practical_scope="raw-spectra dialect is unknown to the current ingestion boundary",
                diagnostics=(
                    "no practical ingestion support is defined for this suffix",
                ),
            )
        )

    supported_count = sum(
        entry.support_state is RawSpectraDialectRealityState.SUPPORTED
        for entry in entries
    )
    partial_count = sum(
        entry.support_state is RawSpectraDialectRealityState.PARTIAL
        for entry in entries
    )
    refused_count = len(entries) - supported_count - partial_count
    return RawSpectraDialectRealityReport(
        entries=tuple(entries),
        supported_count=supported_count,
        partial_count=partial_count,
        refused_count=refused_count,
        note=(
            "raw-spectra dialect reality distinguishes standard mzML decoding support from exchange-only MGF behavior and refused vendor-native raw surfaces"
        ),
    )


def _local_name(tag: str) -> str:
    if "}" not in tag:
        return tag
    return tag.rsplit("}", 1)[1]


def _parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
