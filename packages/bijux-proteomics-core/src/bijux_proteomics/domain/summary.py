"""Core-owned domain summary primitives for sequence and structure analytics."""

from __future__ import annotations

from dataclasses import dataclass, field


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


@dataclass(frozen=True)
class SecondarySummary:
    """Summary of secondary structure ratios."""

    pct_helix: float = 0.0
    pct_sheet: float = 0.0
    pct_coil: float = 0.0
    ss8_pct: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class TertiarySummary:
    """Summary of tertiary structure quality signals."""

    mean_plddt: float | None = None
    plddt_bands: dict[str, float] = field(default_factory=dict)
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
