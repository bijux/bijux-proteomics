# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Iteration-04 identification, FDR, and inference capability surfaces."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class TargetDecoyStrategyKind(StrEnum):
    """Supported target-decoy confidence strategies."""

    CONCATENATED = "concatenated"
    SEPARATE = "separate"
    PICKED = "picked"
    ENTRAPMENT = "entrapment"
    CUSTOM = "custom"
    NO_DECOY = "no_decoy"


class TargetDecoyStrategyDefinition(JsonModel):
    """One strategy definition inside the target-decoy registry."""

    model_config = ConfigDict(extra="forbid")

    strategy_kind: TargetDecoyStrategyKind
    display_name: str = Field(..., min_length=1)
    supports_psm: bool = True
    supports_peptide: bool = True
    supports_protein: bool = True
    supports_ptm: bool = False
    supports_group: bool = False
    requires_decoy_channel: bool = True
    reproducibility_notes: tuple[str, ...] = Field(default_factory=tuple)
    cautionary_notes: tuple[str, ...] = Field(default_factory=tuple)


class TargetDecoyStrategyRegistry(JsonModel):
    """Stable registry over supported target-decoy confidence strategies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[TargetDecoyStrategyDefinition, ...] = Field(default_factory=tuple)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


def _default_target_decoy_strategy_definitions() -> tuple[TargetDecoyStrategyDefinition, ...]:
    return (
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.CONCATENATED,
            display_name="Concatenated target-decoy",
            supports_ptm=True,
            supports_group=True,
            requires_decoy_channel=True,
            reproducibility_notes=(
                "record target and decoy hits in one ranked list with fixed score orientation",
                "persist tie-handling and threshold policy alongside accepted evidence",
            ),
            cautionary_notes=(
                "mixing independently filtered runs can invalidate concatenated ranking assumptions",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.SEPARATE,
            display_name="Separate target and decoy searches",
            supports_ptm=True,
            supports_group=True,
            requires_decoy_channel=True,
            reproducibility_notes=(
                "store per-run target and decoy score distributions before merge",
                "normalize separate-run score scales before computing q-values",
            ),
            cautionary_notes=(
                "unscaled score distributions can bias separate-search confidence estimates",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.PICKED,
            display_name="Picked protein strategy",
            supports_group=True,
            requires_decoy_channel=True,
            reproducibility_notes=(
                "retain target/decoy competition outcomes at the protein accession level",
            ),
            cautionary_notes=(
                "picked strategy assumes deterministic target-decoy accession pairing",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.ENTRAPMENT,
            display_name="Entrapment-aware strategy",
            supports_group=True,
            requires_decoy_channel=False,
            reproducibility_notes=(
                "capture entrapment set composition and accession versioning",
                "separate entrapment-derived calibration from primary q-value thresholds",
            ),
            cautionary_notes=(
                "entrapment references must remain disjoint from biological targets",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.CUSTOM,
            display_name="Custom confidence strategy",
            supports_group=True,
            requires_decoy_channel=False,
            reproducibility_notes=(
                "declare custom confidence formula inputs and deterministic ordering keys",
            ),
            cautionary_notes=(
                "custom strategies require explicit validation before reuse across studies",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.NO_DECOY,
            display_name="No-decoy advisory strategy",
            supports_psm=True,
            supports_peptide=True,
            supports_protein=False,
            supports_ptm=False,
            supports_group=False,
            requires_decoy_channel=False,
            reproducibility_notes=(
                "report confidence as advisory and avoid hard biological acceptance claims",
            ),
            cautionary_notes=(
                "missing decoy evidence prevents comparative FDR validation",
            ),
        ),
    )


def build_target_decoy_strategy_registry(
    *,
    custom_entries: tuple[TargetDecoyStrategyDefinition, ...] = (),
) -> TargetDecoyStrategyRegistry:
    """Build the stable target-decoy strategy registry with optional custom entries."""
    entries_by_kind = {
        entry.strategy_kind: entry
        for entry in _default_target_decoy_strategy_definitions()
    }
    for entry in custom_entries:
        entries_by_kind[entry.strategy_kind] = entry
    entries = tuple(sorted(entries_by_kind.values(), key=lambda entry: entry.strategy_kind.value))
    payload = [entry.to_dict() for entry in entries]
    reproducibility_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return TargetDecoyStrategyRegistry(
        entries=entries,
        reproducibility_hash=reproducibility_hash,
    )
