# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum loading helpers for similarity and library comparison workflows."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.io import SpectrumModel, parse_mgf, parse_mzml


def _load_similarity_spectra(
    input_path: Path, *, kind: str
) -> tuple[SpectrumModel, ...]:
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise ValueError(
                f"cannot infer spectrum input kind for {input_path.name!r}; "
                "use --query-kind/--reference-kind mgf or mzml"
            )
    if resolved_kind == "mgf":
        return cast(tuple[SpectrumModel, ...], parse_mgf(input_path).accepted_spectra)
    if resolved_kind == "mzml":
        return cast(tuple[SpectrumModel, ...], parse_mzml(input_path).accepted_spectra)
    raise ValueError("spectrum similarity supports only mgf and mzml inputs")


def _select_similarity_spectrum(
    spectra: tuple[SpectrumModel, ...],
    *,
    input_path: Path,
    spectrum_id: str | None,
) -> SpectrumModel:
    if not spectra:
        raise ValueError(
            f"{input_path.name!r} does not contain an accepted spectrum for comparison"
        )
    if spectrum_id is None:
        return spectra[0]
    try:
        return next(item for item in spectra if item.spectrum_id == spectrum_id)
    except StopIteration as exc:
        raise ValueError(
            f"unknown spectrum id {spectrum_id!r} in {input_path.name!r}"
        ) from exc


__all__ = [
    "_load_similarity_spectra",
    "_select_similarity_spectrum",
]
