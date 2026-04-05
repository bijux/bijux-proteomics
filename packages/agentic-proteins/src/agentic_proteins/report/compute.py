# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Report computation primitives (metrics, summaries, analysis)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import numbers
from typing import Any, NewType, cast

from loguru import logger
import numpy as np

from agentic_proteins.core.hashing import sha256_hex
from agentic_proteins.report.model import Report

Percentage = NewType("Percentage", float)  # [0,100]
Probability = NewType("Probability", float)  # [0,1]


class PLDDTBand(str, Enum):
    """pLDDT confidence bands."""

    GE90 = "≥90"
    B70_90 = "70–90"
    B50_70 = "50–70"
    LT50 = "<50"


class SS8(str, Enum):
    """8-state secondary structure labels from DSSP."""

    H = "H"
    E = "E"
    G = "G"
    I = "I"  # noqa: E741 - SS8 uses 'I' for pi-helix; keep canonical label
    B = "B"
    T = "T"
    S = "S"
    C = "C"


@dataclass(frozen=True)
class PrimarySummary:
    """Summary of primary structure metrics."""

    length: int
    aa_composition: dict[str, float] = field(default_factory=dict)
    gravy: float | None = None
    isoelectric_point: float | None = None
    pct_disorder: float | None = None
    pct_low_complexity: float | None = None
    has_signal_peptide: bool | None = None
    has_tm_segments: bool | None = None

    @property
    def pI(self) -> float | None:  # noqa: N802
        """pI."""
        return self.isoelectric_point

    def __post_init__(self) -> None:
        """__post_init__."""
        aa_sum = sum(self.aa_composition.values())
        if abs(aa_sum - 100.0) > 1e-6:
            logger.warning(
                "AA composition sums to %s, not 100; tolerating but check input",
                aa_sum,
            )
        for pct_field in (self.pct_disorder, self.pct_low_complexity):
            if pct_field is not None and not (0.0 <= pct_field <= 100.0):
                logger.warning(
                    "Percentage field out of [0,100]: %s; tolerating", pct_field
                )

    def __repr__(self) -> str:
        """__repr__."""
        return f"PrimarySummary(length={self.length}, gravy={self.gravy})"


@dataclass(frozen=True)
class SecondarySummary:
    """Summary of secondary structure metrics."""

    pct_helix: Percentage = cast(Percentage, 0.0)
    pct_sheet: Percentage = cast(Percentage, 0.0)
    pct_coil: Percentage = cast(Percentage, 0.0)
    ss8_pct: dict[SS8, Percentage] = field(default_factory=dict)
    q3: Percentage | None = None
    q8: Percentage | None = None
    sov99: Percentage | None = None

    def __post_init__(self) -> None:
        """__post_init__."""
        ss8_sum = sum(self.ss8_pct.values())
        if abs(ss8_sum - 100.0) > 1e-6:
            logger.warning(
                "ss8_pct sum to %s, not 100; tolerating but check input", ss8_sum
            )
        for pct_field in [
            self.pct_helix,
            self.pct_sheet,
            self.pct_coil,
            self.q3,
            self.q8,
            self.sov99,
        ]:
            if pct_field is not None and not (0.0 <= pct_field <= 100.0):
                logger.warning(
                    "Percentage field out of [0,100]: %s; tolerating", pct_field
                )

    def __repr__(self) -> str:
        """__repr__."""
        return (
            f"SecondarySummary(pct_helix={self.pct_helix}, pct_sheet={self.pct_sheet})"
        )


@dataclass(frozen=True)
class TertiarySummary:
    """Summary of tertiary structure metrics."""

    mean_plddt: float
    plddt_bands: dict[PLDDTBand, Percentage] = field(default_factory=dict)
    pae_median: float | None = None
    pae_q90: float | None = None
    rg: float | None = None
    sasa: float | None = None
    hbonds: int | None = None
    rama_outliers_pct: float | None = None
    clashscore: float | None = None
    rmsd: float | None = None
    gdt_ts: float | None = None
    gdt_ha: float | None = None
    tm_score: float | None = None
    lddt: float | None = None
    n_interfaces: int | None = None
    buried_sasa: float | None = None
    irmsd: float | None = None
    dockq: float | None = None

    def __post_init__(self) -> None:
        """__post_init__."""
        object.__setattr__(self, "plddt_bands", self._normalize_bands(self.plddt_bands))
        band_sum = sum(self.plddt_bands.values())
        if abs(band_sum - 100.0) > 1e-6:
            logger.warning(
                "pLDDT bands sum to %s, not 100; tolerating but check input", band_sum
            )
        for v in self.plddt_bands.values():
            if v is not None and not (0.0 <= v <= 100.0):
                raise ValueError(f"plddt_bands values must be in [0, 100]; got {v}")
        for pct_field in [self.rama_outliers_pct]:
            if pct_field is not None and not (0.0 <= pct_field <= 100.0):
                logger.warning(
                    "Percentage field out of [0,100]: %s; tolerating", pct_field
                )
        for prob_field in [self.tm_score, self.dockq, self.lddt]:
            if prob_field is not None and not (0.0 <= prob_field <= 1.0):
                logger.warning(
                    "Probability field out of [0,1]: %s; tolerating", prob_field
                )

    def _normalize_bands(
        self, bands: Mapping[str, float]
    ) -> dict[PLDDTBand, Percentage]:
        """_normalize_bands."""
        norm_bands: dict[PLDDTBand, Percentage] = {}
        for band in PLDDTBand.__members__.values():
            k = band.value
            alt_k = k.replace("≥", ">=").replace("–", "-")
            v = bands.get(k, bands.get(alt_k, 0.0))
            pv = (
                float(v)
                if isinstance(v, numbers.Real) and np.isfinite(float(v))
                else 0.0
            )
            norm_bands[band] = Percentage(pv)
        return norm_bands

    def __repr__(self) -> str:
        """__repr__."""
        return f"TertiarySummary(mean_plddt={self.mean_plddt}, rmsd={self.rmsd})"


def assert_band_sum(bands: dict[PLDDTBand, Percentage], tol: float = 1.0) -> None:
    """assert_band_sum."""
    s = sum(bands.values())
    if abs(s - 100.0) > tol:
        raise AssertionError(f"Band sum {s} != 100 ± {tol}")


@dataclass(frozen=True)
class Metrics:
    """Aggregated metrics from primary, secondary, and tertiary summaries."""

    primary: PrimarySummary
    secondary: SecondarySummary
    tertiary: TertiarySummary
    ref_residues: int | None = None
    n_matched_pairs: int | None = None
    seq_identity: Probability | None = None
    gap_fraction: Probability | None = None

    def __post_init__(self) -> None:
        """__post_init__."""
        for prob_field in [self.seq_identity, self.gap_fraction]:
            if prob_field is not None and not (0.0 <= prob_field <= 1.0):
                logger.warning(
                    "Probability field out of [0,1]: %s; tolerating", prob_field
                )

    @property
    def cov_pred(self) -> Percentage | None:
        """cov_pred."""
        if self.n_matched_pairs is None or self.primary.length <= 0:
            return None
        return Percentage(self.n_matched_pairs / self.primary.length * 100)

    @property
    def cov_ref(self) -> Percentage | None:
        """cov_ref."""
        if (
            self.n_matched_pairs is None
            or self.ref_residues is None
            or self.ref_residues <= 0
        ):
            return None
        return Percentage(self.n_matched_pairs / self.ref_residues * 100)

    def __repr__(self) -> str:
        """__repr__."""
        return (
            "Metrics(primary="
            f"{repr(self.primary)}, secondary={repr(self.secondary)}, tertiary={repr(self.tertiary)})"
        )


def compute_report_warnings(metrics: Metrics) -> list[str]:
    """compute_report_warnings."""
    warnings: list[str] = []
    if metrics.primary.length <= 0:
        raise ValueError("length must be > 0")
    if np.isnan(metrics.tertiary.mean_plddt) or metrics.tertiary.mean_plddt < 70:
        warnings.append("Low overall confidence (mean pLDDT < 70)")
    if metrics.tertiary.plddt_bands.get(PLDDTBand.LT50, 0.0) > 20:
        warnings.append("Large low-confidence fraction (<50 pLDDT > 20%)")
    if metrics.primary.gravy is not None and (
        metrics.primary.gravy < -2 or metrics.primary.gravy > 2
    ):
        warnings.append(
            "Unusual GRAVY score; potential aggregation or solubility issues"
        )
    if any(np.isnan(v) for v in [metrics.tertiary.mean_plddt, metrics.primary.gravy]):
        warnings.append("NaN values clipped; check input data")
    return warnings


def report_hash(report: Report) -> str:
    """report_hash."""
    norm_json = json.dumps(json_safe(asdict(report)), sort_keys=True)
    return sha256_hex(norm_json)


def compare_reports(report: Report, other: Report) -> dict[str, Any]:
    """compare_reports."""
    a, b = report.metrics, other.metrics

    def d(x, y):
        """d."""
        return None if (x is None or y is None) else (float(x) - float(y))

    def delta_pct(x, y):
        """delta_pct."""
        if x is None or y is None or y == 0:
            return None
        return (float(x) - float(y)) / float(y) * 100

    def is_significant(delta: float | None, thresh: float = 5.0) -> bool:
        """is_significant."""
        return delta is not None and abs(delta) > thresh

    comp = {
        "diff": [],
        "primary": {
            "length_delta": d(a.primary.length, b.primary.length),
            "seq_identity": a.seq_identity,
            "gap_fraction": a.gap_fraction,
        },
        "secondary": {
            "q3": a.secondary.q3,
            "q8": a.secondary.q8,
            "sov99": a.secondary.sov99,
            "pct_helix_delta": d(a.secondary.pct_helix, b.secondary.pct_helix),
            "pct_helix_delta_pct": delta_pct(
                a.secondary.pct_helix, b.secondary.pct_helix
            ),
            "pct_sheet_delta": d(a.secondary.pct_sheet, b.secondary.pct_sheet),
            "pct_sheet_delta_pct": delta_pct(
                a.secondary.pct_sheet, b.secondary.pct_sheet
            ),
            "pct_coil_delta": d(a.secondary.pct_coil, b.secondary.pct_coil),
            "pct_coil_delta_pct": delta_pct(a.secondary.pct_coil, b.secondary.pct_coil),
        },
        "tertiary": {
            "rmsd_self": a.tertiary.rmsd,
            "tm_score_self": a.tertiary.tm_score,
            "gdt_ts_self": a.tertiary.gdt_ts,
            "gdt_ha_self": a.tertiary.gdt_ha,
            "lddt_self": a.tertiary.lddt,
            "pae_median_self": a.tertiary.pae_median,
        },
    }

    for section, fields in [
        ("primary", comp["primary"]),
        ("secondary", comp["secondary"]),
        ("tertiary", comp["tertiary"]),
    ]:
        for k, v in fields.items():
            if "_delta" in k:
                old = getattr(b, k.replace("_delta", ""), None)
                new = getattr(a, k.replace("_delta", ""), None)
                delta = v
                pct = fields.get(k + "_pct", None)
                sig = is_significant(abs(delta or 0), thresh=5.0 if "pct" in k else 0.1)
                comp["diff"].append(
                    {
                        "path": f"metrics/{section}/{k.replace('_delta', '')}",
                        "old": old,
                        "new": new,
                        "delta": delta,
                        "delta_pct": pct,
                        "significant": sig,
                    }
                )

    parts = []
    if comp["tertiary"]["tm_score_self"] is not None:
        parts.append(f"TM={comp['tertiary']['tm_score_self']:.3f}")
    if comp["tertiary"]["rmsd_self"] is not None:
        parts.append(f"RMSD={comp['tertiary']['rmsd_self']:.2f} Å")
    if a.secondary.q3 is not None:
        parts.append(f"Q3={a.secondary.q3:.1f}%")
    if a.tertiary.pae_median is not None:
        parts.append(f"pAE~{a.tertiary.pae_median:.1f}")

    comp["text"] = " | ".join(parts) if parts else "No comparative metrics available."
    return comp


def json_safe(x: Any) -> Any:
    """json_safe."""
    if isinstance(x, (bool, str, int, type(None))):
        return x
    if isinstance(x, numbers.Real):
        xf = float(x)
        if np.isnan(xf) or np.isinf(xf):
            return None
        return xf
    if isinstance(x, dict):
        return {k: json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_safe(v) for v in x]
    raise TypeError(f"Unserializable type: {type(x)}")
