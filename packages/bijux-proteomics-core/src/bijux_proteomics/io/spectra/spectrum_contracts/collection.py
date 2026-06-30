# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum collection, lookup, provenance, and MGF rendering helpers."""

from __future__ import annotations

from collections.abc import Iterator
import csv
import hashlib
import io
from pathlib import Path
import re

from bijux_proteomics.io.raw.mgf_streaming import (
    iter_mgf_spectra as _iter_mgf_spectra,
)
from bijux_proteomics.io.raw.mgf_streaming import (
    parse_mgf as _parse_mgf,
)
from bijux_proteomics_foundation import DocumentSchema

from bijux_proteomics.io.spectra.spectrum_contracts.models import (
    MgfParseReport,
    SpectrumCollectionSummary,
    SpectrumDistributionRow,
    SpectrumLibrarySimilarityReport,
    SpectrumLookupIndex,
    SpectrumModel,
    SpectrumProvenanceManifest,
    SpectrumSummaryTableReport,
)


def _scan_number_from_text(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"scan=(\d+)", value, flags=re.IGNORECASE)
    if match is not None:
        return int(match.group(1))
    if value.isdigit():
        return int(value)
    return None


def normalize_spectrum_scan_key(
    spectrum_or_text: SpectrumModel | str | None,
) -> str | None:
    """Normalize one scan-like identifier onto a stable key."""
    if spectrum_or_text is None:
        return None
    if isinstance(spectrum_or_text, SpectrumModel):
        candidates = (
            spectrum_or_text.native_id,
            spectrum_or_text.spectrum_id,
            spectrum_or_text.title,
        )
        scan_number = spectrum_or_text.scan_number
        if scan_number is not None:
            return f"scan:{scan_number}"
        for candidate in candidates:
            parsed = _scan_number_from_text(candidate)
            if parsed is not None:
                return f"scan:{parsed}"
        return None
    parsed = _scan_number_from_text(spectrum_or_text)
    if parsed is not None:
        return f"scan:{parsed}"
    return None


def iter_mgf_spectra(path: Path) -> Iterator[SpectrumModel]:
    """Yield accepted MGF spectra one block at a time from a streaming parse."""
    yield from _iter_mgf_spectra(path)


def parse_mgf(path: Path) -> MgfParseReport:
    """Parse an MGF file into stable spectrum contracts through streaming IO."""
    return _parse_mgf(path)


def build_spectrum_collection_summary(
    parse_report: MgfParseReport,
) -> SpectrumCollectionSummary:
    """Build a compact summary for one parsed spectrum collection."""
    counts_by_charge: dict[str, int] = {}
    issue_counts: dict[str, int] = {}
    total_peak_count = 0
    for spectrum in parse_report.accepted_spectra:
        total_peak_count += len(spectrum.peaks)
        key = (
            "unknown"
            if spectrum.precursor_charge is None
            else str(spectrum.precursor_charge)
        )
        counts_by_charge[key] = counts_by_charge.get(key, 0) + 1
    for block in parse_report.rejected_blocks:
        for issue in block.issues:
            issue_counts[issue.code] = issue_counts.get(issue.code, 0) + 1
    spectrum_count = len(parse_report.accepted_spectra)
    return SpectrumCollectionSummary(
        spectrum_count=spectrum_count,
        rejected_block_count=len(parse_report.rejected_blocks),
        total_peak_count=total_peak_count,
        average_peak_count=(total_peak_count / spectrum_count)
        if spectrum_count
        else 0.0,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        issue_counts=dict(sorted(issue_counts.items())),
    )


def _bucket_count(
    value: int, *, buckets: tuple[tuple[str, int, int | None], ...]
) -> str:
    for label, lower, upper in buckets:
        if value < lower:
            continue
        if upper is None or value <= upper:
            return label
    return buckets[-1][0]


def _bucket_float(
    value: float, *, buckets: tuple[tuple[str, float, float | None], ...]
) -> str:
    for label, lower, upper in buckets:
        if value < lower:
            continue
        if upper is None or value <= upper:
            return label
    return buckets[-1][0]


def build_spectrum_summary_table_report(
    spectra: tuple[SpectrumModel, ...],
    *,
    source_kind: str,
    rejected_count: int = 0,
) -> SpectrumSummaryTableReport:
    """Build reviewer-facing spectrum summary tables over accepted spectra."""
    ms1_count = 0
    ms2_count = 0
    unknown_ms_level_count = 0
    charge_counts: dict[str, int] = {}
    precursor_counts: dict[str, int] = {}
    peak_counts: dict[str, int] = {}
    retention_times: list[float] = []

    mz_buckets = (
        ("0-399", 0.0, 399.999999),
        ("400-599", 400.0, 599.999999),
        ("600-799", 600.0, 799.999999),
        ("800-999", 800.0, 999.999999),
        ("1000+", 1000.0, None),
    )
    peak_buckets = (
        ("1-24", 1, 24),
        ("25-49", 25, 49),
        ("50-99", 50, 99),
        ("100-199", 100, 199),
        ("200+", 200, None),
    )

    ms_level_policy = "reported"
    for spectrum in spectra:
        ms_level = spectrum.ms_level
        if source_kind == "mgf" and ms_level is None:
            ms_level_policy = "mgf_assumed_ms2"
            ms2_count += 1
        elif ms_level == 1:
            ms1_count += 1
        elif ms_level == 2:
            ms2_count += 1
        else:
            unknown_ms_level_count += 1

        if spectrum.precursor_charge is None:
            charge_key = "unknown"
        elif spectrum.precursor_charge >= 5:
            charge_key = "5+"
        else:
            charge_key = str(spectrum.precursor_charge)
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1

        precursor_bucket = _bucket_float(
            spectrum.precursor_mz,
            buckets=mz_buckets,
        )
        precursor_counts[precursor_bucket] = (
            precursor_counts.get(precursor_bucket, 0) + 1
        )

        peak_bucket = _bucket_count(
            len(spectrum.peaks),
            buckets=peak_buckets,
        )
        peak_counts[peak_bucket] = peak_counts.get(peak_bucket, 0) + 1

        if spectrum.retention_time_seconds is not None:
            retention_times.append(spectrum.retention_time_seconds)

    charge_distribution = tuple(
        SpectrumDistributionRow(bucket=bucket, count=charge_counts.get(bucket, 0))
        for bucket in ("unknown", "1", "2", "3", "4", "5+")
        if bucket != "5+" or charge_counts.get("5+", 0) > 0
    )

    precursor_distribution = tuple(
        SpectrumDistributionRow(bucket=label, count=precursor_counts.get(label, 0))
        for label, _lower, _upper in mz_buckets
    )
    peak_distribution = tuple(
        SpectrumDistributionRow(bucket=label, count=peak_counts.get(label, 0))
        for label, _lower, _upper in peak_buckets
    )

    return SpectrumSummaryTableReport(
        source_kind=source_kind,
        ms_level_policy=ms_level_policy,
        spectrum_count=len(spectra),
        rejected_count=rejected_count,
        ms1_spectrum_count=ms1_count,
        ms2_spectrum_count=ms2_count,
        unknown_ms_level_count=unknown_ms_level_count,
        retention_time_min_seconds=min(retention_times) if retention_times else None,
        retention_time_max_seconds=max(retention_times) if retention_times else None,
        charge_distribution=charge_distribution,
        precursor_mz_distribution=precursor_distribution,
        peak_count_distribution=peak_distribution,
    )


def _render_tsv(header: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def render_spectrum_summary_tsv(report: SpectrumSummaryTableReport) -> str:
    """Render one compact summary table for a spectrum run report."""
    return _render_tsv(
        (
            "source_kind",
            "ms_level_policy",
            "spectrum_count",
            "rejected_count",
            "ms1_spectrum_count",
            "ms2_spectrum_count",
            "unknown_ms_level_count",
            "retention_time_min_seconds",
            "retention_time_max_seconds",
        ),
        (
            (
                report.source_kind,
                report.ms_level_policy,
                report.spectrum_count,
                report.rejected_count,
                report.ms1_spectrum_count,
                report.ms2_spectrum_count,
                report.unknown_ms_level_count,
                report.retention_time_min_seconds,
                report.retention_time_max_seconds,
            ),
        ),
    )


def render_spectrum_distribution_tsv(
    rows: tuple[SpectrumDistributionRow, ...],
    *,
    distribution_name: str,
) -> str:
    """Render one stable spectrum distribution table."""
    return _render_tsv(
        ("distribution", "bucket", "count"),
        tuple((distribution_name, row.bucket, row.count) for row in rows),
    )


def render_spectrum_similarity_tsv(
    report: SpectrumLibrarySimilarityReport,
) -> str:
    """Render one stable ranked spectrum-similarity table."""
    return _render_tsv(
        (
            "rank",
            "reference_spectrum_id",
            "classification",
            "score",
            "matched_peak_count",
            "reference_peak_count",
            "query_peak_count",
            "reference_explained_intensity_fraction",
            "query_explained_intensity_fraction",
        ),
        tuple(
            (
                row.rank,
                row.reference_spectrum_id,
                row.classification.value,
                row.score,
                row.matched_peak_count,
                row.reference_peak_count,
                row.query_peak_count,
                row.reference_explained_intensity_fraction,
                row.query_explained_intensity_fraction,
            )
            for row in report.matches
        ),
    )


def build_spectrum_lookup_index(
    spectra: tuple[SpectrumModel, ...],
) -> SpectrumLookupIndex:
    """Build stable lookup maps by native ID, title, scan number, and scan key."""
    native_id_index: dict[str, list[str]] = {}
    title_index: dict[str, list[str]] = {}
    scan_number_index: dict[str, list[str]] = {}
    scan_key_index: dict[str, list[str]] = {}
    normalized_spectra = tuple(sorted(spectra, key=lambda item: item.spectrum_id))
    for spectrum in normalized_spectra:
        if spectrum.native_id:
            native_id_index.setdefault(spectrum.native_id, []).append(
                spectrum.spectrum_id
            )
        if spectrum.title:
            title_index.setdefault(spectrum.title, []).append(spectrum.spectrum_id)
        if spectrum.scan_number is not None:
            scan_number_index.setdefault(str(spectrum.scan_number), []).append(
                spectrum.spectrum_id
            )
        scan_key = normalize_spectrum_scan_key(spectrum)
        if scan_key is not None:
            scan_key_index.setdefault(scan_key, []).append(spectrum.spectrum_id)
    return SpectrumLookupIndex(
        spectra=normalized_spectra,
        native_id_index={
            key: tuple(values) for key, values in sorted(native_id_index.items())
        },
        title_index={key: tuple(values) for key, values in sorted(title_index.items())},
        scan_number_index={
            key: tuple(values) for key, values in sorted(scan_number_index.items())
        },
        scan_key_index={
            key: tuple(values) for key, values in sorted(scan_key_index.items())
        },
    )


def lookup_spectra(
    index: SpectrumLookupIndex,
    *,
    native_id: str | None = None,
    title: str | None = None,
    scan_number: int | None = None,
    scan_key: str | None = None,
) -> tuple[SpectrumModel, ...]:
    """Look up spectra by one stable key family."""
    if (
        sum(query is not None for query in (native_id, title, scan_number, scan_key))
        != 1
    ):
        raise ValueError(
            "exactly one of native_id, title, scan_number, or scan_key must be provided"
        )
    if native_id is not None:
        matched_ids = index.native_id_index.get(native_id, ())
    elif title is not None:
        matched_ids = index.title_index.get(title, ())
    elif scan_number is not None:
        matched_ids = index.scan_number_index.get(str(scan_number), ())
    else:
        normalized_key = normalize_spectrum_scan_key(scan_key)
        matched_ids = index.scan_key_index.get(normalized_key or "", ())
    spectra_by_id = {spectrum.spectrum_id: spectrum for spectrum in index.spectra}
    return tuple(spectra_by_id[spectrum_id] for spectrum_id in matched_ids)


def build_spectrum_provenance_manifest(
    *,
    source_path: Path,
    parse_report: MgfParseReport,
) -> SpectrumProvenanceManifest:
    """Build a stable provenance manifest for one MGF parse run."""
    issue_counts = build_spectrum_collection_summary(parse_report).issue_counts
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SpectrumProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        total_blocks=parse_report.total_blocks,
        accepted_spectra=len(parse_report.accepted_spectra),
        rejected_blocks=len(parse_report.rejected_blocks),
        issue_counts=issue_counts,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def render_mgf(spectra: tuple[SpectrumModel, ...]) -> str:
    """Render stable spectrum contracts into MGF text."""
    lines: list[str] = []
    for spectrum in spectra:
        lines.append("BEGIN IONS")
        lines.append(f"TITLE={spectrum.title or spectrum.spectrum_id}")
        if spectrum.title is None or spectrum.title != spectrum.spectrum_id:
            lines.append(f"SCANS={spectrum.spectrum_id}")
        pepmass = f"PEPMASS={spectrum.precursor_mz:.6f}".rstrip("0").rstrip(".")
        if spectrum.precursor_intensity is not None:
            pepmass += " " + f"{spectrum.precursor_intensity:.6f}".rstrip("0").rstrip(
                "."
            )
        lines.append(pepmass)
        if spectrum.precursor_charge is not None:
            lines.append(f"CHARGE={spectrum.precursor_charge}+")
        if spectrum.retention_time_seconds is not None:
            lines.append(
                f"RTINSECONDS={spectrum.retention_time_seconds:.4f}".rstrip("0").rstrip(
                    "."
                )
            )
        for peak in spectrum.peaks:
            lines.append(
                f"{peak.mz:.6f}".rstrip("0").rstrip(".")
                + " "
                + f"{peak.intensity:.6f}".rstrip("0").rstrip(".")
            )
        lines.append("END IONS")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "build_spectrum_collection_summary",
    "build_spectrum_lookup_index",
    "build_spectrum_provenance_manifest",
    "build_spectrum_summary_table_report",
    "iter_mgf_spectra",
    "lookup_spectra",
    "normalize_spectrum_scan_key",
    "parse_mgf",
    "render_mgf",
    "render_spectrum_distribution_tsv",
    "render_spectrum_similarity_tsv",
    "render_spectrum_summary_tsv",
]
