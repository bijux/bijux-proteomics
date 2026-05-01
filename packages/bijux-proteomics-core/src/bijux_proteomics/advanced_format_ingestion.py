# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced ingestion boundaries for proteomics exchange formats."""

from __future__ import annotations

import csv
from pathlib import Path

from defusedxml import ElementTree as ET
from pydantic import ConfigDict, Field

from bijux_proteomics.formats import parse_mzml
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


class MzmlDecodingSupportReport(JsonModel):
    """Decoding capability report over one mzML binary-array surface."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    spectrum_count: int = Field(..., ge=0)
    accepted_spectrum_count: int = Field(..., ge=0)
    rejected_spectrum_count: int = Field(..., ge=0)
    compression_accessions: tuple[str, ...] = Field(default_factory=tuple)
    precision_accessions: tuple[str, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


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


def parse_mzidentml_or_refuse(path: Path) -> MzIdentMlIngestionReport:
    """Parse mzIdentML core identification surfaces or return precise refusal details."""
    root = ET.parse(path).getroot()
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
        field
        for fields in headers_by_prefix.values()
        for field in fields
    }
    unsupported = {
        field
        for field in observed_headers
        if field.startswith("opt_global_") or field.startswith("opt_assay[")
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
            supported=False,
            required_conversion="convert idXML to normalized PSM TSV or mzIdentML before ingestion",
            diagnostics=(
                "idXML root detected",
                "native idXML mapping is not yet guaranteed to preserve all metadata fields",
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


def inspect_mzml_decoding_support(path: Path) -> MzmlDecodingSupportReport:
    """Inspect mzML binary arrays and summarize decoding support boundaries."""
    root = ET.parse(path).getroot()
    compression: set[str] = set()
    precision: set[str] = set()
    for param in root.findall(".//{*}cvParam"):
        accession = param.attrib.get("accession", "").strip()
        if not accession:
            continue
        if accession in {
            "MS:1000574",  # zlib compression
            "MS:1000576",  # no compression
            "MS:1002312",  # numpress linear
            "MS:1002313",  # numpress pic
            "MS:1002314",  # numpress slof
        }:
            compression.add(accession)
        if accession in {
            "MS:1000521",  # 32-bit float
            "MS:1000523",  # 64-bit float
            "MS:1000519",  # 32-bit integer
            "MS:1000522",  # 64-bit integer
        }:
            precision.add(accession)

    parse_report = parse_mzml(path)
    issue_codes = {
        issue.code
        for rejected in parse_report.rejected_spectra
        for issue in rejected.issues
    }
    supported = not issue_codes.intersection(
        {"unsupported_binary_compression", "unsupported_binary_precision"}
    )
    diagnostics = (
        "mzML decoding supports zlib/no-compression float arrays",
        "unsupported compression or precision is reported with explicit issue codes",
    )
    if not supported:
        diagnostics = diagnostics + (
            "this file includes unsupported binary decoding settings for current ingestion boundaries",
        )
    return MzmlDecodingSupportReport(
        supported=supported,
        spectrum_count=parse_report.total_spectra,
        accepted_spectrum_count=len(parse_report.accepted_spectra),
        rejected_spectrum_count=len(parse_report.rejected_spectra),
        compression_accessions=tuple(sorted(compression)),
        precision_accessions=tuple(sorted(precision)),
        diagnostics=diagnostics,
    )


def parse_chromatogram_qc_table(path: Path) -> ChromatogramQcIngestionReport:
    """Parse TIC/BPC chromatogram QC tables and distinguish unknown from failed metrics."""
    reader = csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t")
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
        text = path.read_text(encoding="utf-8")
        entry_count = text.count("\nName:")
        if text.startswith("Name:"):
            entry_count += 1
        return SpectrumLibraryBoundaryReport(
            format_name="MSP",
            supported=True,
            support_mode="parse_only",
            entry_count=entry_count,
            mapped_fields=("Name", "MW", "Comment", "Num peaks"),
            diagnostics=(
                "MSP library detected with parse-only support mode",
                "normalization preserves entry counting and key header fields",
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
