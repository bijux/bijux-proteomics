# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Streaming MGF parsing with accepted-spectrum and rejected-block outcomes."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.spectra.spectrum_contracts.models import (
        MgfParseReport,
        RejectedSpectrumBlock,
        SpectrumModel,
        SpectrumPeak,
        SpectrumValidationIssue,
    )


class MgfBlockParseResult(JsonModel):
    """One streamed MGF block outcome."""

    model_config = ConfigDict(extra="forbid")

    block_index: int = Field(..., ge=1)
    accepted_spectrum: SpectrumModel | None = None
    rejected_block: RejectedSpectrumBlock | None = None


@dataclass(slots=True)
class _MgfBlock:
    block_index: int
    title: str | None = None
    spectrum_id: str | None = None
    precursor_mz: float | None = None
    precursor_intensity: float | None = None
    precursor_charge: int | None = None
    retention_time_seconds: float | None = None
    peaks: list[SpectrumPeak] = field(default_factory=list)
    issues: list[SpectrumValidationIssue] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)


def _scan_number_from_text(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"scan=(\d+)", value, flags=re.IGNORECASE)
    if match is not None:
        return int(match.group(1))
    if value.isdigit():
        return int(value)
    return None


def _issue(
    block_index: int,
    code: str,
    message: str,
    *,
    field: str | None = None,
    line_number: int | None = None,
    raw_line: str | None = None,
) -> SpectrumValidationIssue:
    from bijux_proteomics.io.spectra.spectrum_contracts.models import (
        SpectrumValidationIssue,
    )

    return SpectrumValidationIssue(
        code=code,
        message=message,
        block_index=block_index,
        field=field,
        line_number=line_number,
        raw_line=raw_line,
    )


def _parse_charge(token: str) -> int:
    normalized = token.strip()
    if not normalized:
        raise ValueError("empty charge token")
    matches = re.findall(r"[+-]?\d+\+*", normalized.replace("and", ","))
    if not matches:
        raise ValueError("invalid charge token")
    charges = {
        int(match.lstrip("+").rstrip("+"))
        for match in matches
        if match.lstrip("+").rstrip("+")
    }
    if not charges:
        raise ValueError("invalid charge token")
    if len(charges) > 1:
        raise ValueError("ambiguous precursor charge list")
    return next(iter(charges))


def _append_mgf_metadata_issue(
    block: _MgfBlock,
    *,
    key: str,
    raw_line: str,
    line_number: int,
    error: ValueError,
) -> None:
    block.issues.append(
        _issue(
            block.block_index,
            f"invalid_{key.lower()}",
            str(error),
            field=key,
            line_number=line_number,
            raw_line=raw_line,
        )
    )


def _parse_mgf_metadata_line(
    block: _MgfBlock,
    *,
    key: str,
    value: str,
    raw_line: str,
    line_number: int,
) -> None:
    try:
        if key == "TITLE":
            block.title = value
            if block.spectrum_id is None:
                block.spectrum_id = value
        elif key in {"SCANS", "SPECTRUMID"}:
            block.spectrum_id = value
        elif key == "PEPMASS":
            block.precursor_mz = float(value.split()[0])
            pieces = value.split()
            if len(pieces) >= 2:
                block.precursor_intensity = float(pieces[1])
        elif key == "CHARGE":
            block.precursor_charge = _parse_charge(value)
        elif key == "RTINSECONDS":
            block.retention_time_seconds = float(value)
        elif key == "RTINMINUTES":
            block.retention_time_seconds = float(value) * 60.0
    except ValueError as exc:
        _append_mgf_metadata_issue(
            block,
            key=key,
            raw_line=raw_line,
            line_number=line_number,
            error=exc,
        )


def _finalize_mgf_block(block: _MgfBlock) -> MgfBlockParseResult:
    from bijux_proteomics.io.spectra import (
        RejectedSpectrumBlock,
        SpectrumModel,
    )

    if block.precursor_mz is None:
        block.issues.append(
            _issue(block.block_index, "missing_precursor_mz", "PEPMASS is required")
        )
    if not block.peaks:
        block.issues.append(
            _issue(block.block_index, "missing_peaks", "at least one peak is required")
        )
    spectrum_id = block.spectrum_id or block.title or f"spectrum-{block.block_index}"
    if block.issues:
        return MgfBlockParseResult(
            block_index=block.block_index,
            rejected_block=RejectedSpectrumBlock(
                block_index=block.block_index,
                title=block.title,
                issues=tuple(block.issues),
                raw_block="\n".join(block.raw_lines),
            ),
        )
    return MgfBlockParseResult(
        block_index=block.block_index,
        accepted_spectrum=SpectrumModel(
            spectrum_id=spectrum_id,
            native_id=block.spectrum_id,
            scan_number=_scan_number_from_text(block.spectrum_id or block.title),
            precursor_mz=block.precursor_mz or 1.0,
            precursor_intensity=block.precursor_intensity,
            precursor_charge=block.precursor_charge,
            retention_time_seconds=block.retention_time_seconds,
            peaks=tuple(block.peaks),
            title=block.title,
        ),
    )


def iter_mgf_parse_results(path: Path) -> Iterator[MgfBlockParseResult]:
    """Yield accepted-spectrum or rejected-block outcomes one MGF block at a time."""

    from bijux_proteomics.io.spectra import SpectrumPeak

    current: _MgfBlock | None = None
    block_index = 0

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped_line = raw_line.rstrip("\n")
            line = stripped_line.strip()
            if not line or line.startswith(("#", ";", "!", "//")):
                continue
            if line.upper() == "BEGIN IONS":
                if current is not None:
                    current.issues.append(
                        _issue(
                            current.block_index,
                            "missing_end_ions",
                            "missing END IONS before next block",
                            line_number=line_number,
                            raw_line=stripped_line,
                        )
                    )
                    yield _finalize_mgf_block(current)
                block_index += 1
                current = _MgfBlock(block_index=block_index)
                current.raw_lines.append(stripped_line)
                continue
            if current is None:
                continue
            current.raw_lines.append(stripped_line)
            if line.upper() == "END IONS":
                yield _finalize_mgf_block(current)
                current = None
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                _parse_mgf_metadata_line(
                    current,
                    key=key.strip().upper(),
                    value=value.strip(),
                    raw_line=stripped_line,
                    line_number=line_number,
                )
                continue
            tokens = line.split()
            if len(tokens) != 2:
                current.issues.append(
                    _issue(
                        current.block_index,
                        "invalid_peak_line",
                        f"invalid peak line {line!r}",
                        field="PEAK",
                        line_number=line_number,
                        raw_line=stripped_line,
                    )
                )
                continue
            try:
                peak = SpectrumPeak(mz=float(tokens[0]), intensity=float(tokens[1]))
            except ValueError as exc:
                current.issues.append(
                    _issue(
                        current.block_index,
                        "invalid_peak_value",
                        str(exc),
                        field="PEAK",
                        line_number=line_number,
                        raw_line=stripped_line,
                    )
                )
                continue
            current.peaks.append(peak)

    if current is not None:
        current.issues.append(
            _issue(
                current.block_index,
                "missing_end_ions",
                "unterminated spectrum block",
            )
        )
        yield _finalize_mgf_block(current)


def iter_mgf_spectra(path: Path) -> Iterator[SpectrumModel]:
    """Yield accepted spectra one MGF block at a time."""

    for result in iter_mgf_parse_results(path):
        if result.accepted_spectrum is not None:
            yield result.accepted_spectrum


def parse_mgf(path: Path) -> MgfParseReport:
    """Aggregate one streamed MGF parse into the stable report contract."""

    from bijux_proteomics.io.spectra.spectrum_contracts.models import MgfParseReport

    accepted: list[SpectrumModel] = []
    rejected: list[RejectedSpectrumBlock] = []
    total_blocks = 0
    for result in iter_mgf_parse_results(path):
        total_blocks = result.block_index
        if result.accepted_spectrum is not None:
            accepted.append(result.accepted_spectrum)
        elif result.rejected_block is not None:
            rejected.append(result.rejected_block)
    return MgfParseReport(
        total_blocks=total_blocks,
        accepted_spectra=tuple(accepted),
        rejected_blocks=tuple(rejected),
    )


def count_mgf_blocks(path: Path) -> int:
    """Count parsed MGF blocks without relying on full-file reads."""

    count = 0
    for result in iter_mgf_parse_results(path):
        count = result.block_index
    return count
