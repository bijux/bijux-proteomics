# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared support helpers for laboratory QC owners."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics_foundation import DocumentSchema, JsonModel, hash_model


def build_document_schema(document_kind: str) -> DocumentSchema:
    """Build one stable generated-document schema for QC artifacts."""
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def stable_sha256(payload: JsonModel) -> str:
    """Hash one QC model with stable JSON ordering."""
    return hash_model(payload)


def hash_file(path: Path) -> str:
    """Hash one input file by bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_run_id(
    run_id: str | None, design_entry: ExperimentalDesignEntry | None
) -> str:
    """Resolve a stable run identifier from explicit or design metadata."""
    if run_id:
        return run_id
    if design_entry and design_entry.spectra_file:
        return Path(design_entry.spectra_file).stem
    if design_entry and design_entry.sample_id:
        return f"{design_entry.sample_id}-run"
    return "run"


def quantile(sorted_values: list[float], fraction: float) -> float:
    """Interpolate one quantile from an already-sorted numeric sequence."""
    if not sorted_values:
        raise ValueError("cannot calculate a quantile for an empty sequence")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    interpolation = position - lower_index
    return sorted_values[lower_index] + (
        (sorted_values[upper_index] - sorted_values[lower_index]) * interpolation
    )


def fraction(count: int, total: int) -> float:
    """Return one safe count fraction."""
    return 0.0 if total == 0 else count / total


def metadata_reference_values(metadata: dict[str, str], key: str) -> tuple[str, ...]:
    """Parse one semicolon-delimited metadata field into stable reference values."""
    value = metadata.get(key, "").strip()
    if not value:
        return ()
    return tuple(sorted({token.strip() for token in value.split(";") if token.strip()}))


def format_metric_value(value: float | None) -> str:
    """Format one observed metric value for stable text rendering."""
    if value is None:
        return ""
    return f"{value:.4f}".rstrip("0").rstrip(".")
