# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification_iteration04 import (
    TargetDecoyStrategyDefinition,
    TargetDecoyStrategyKind,
    build_target_decoy_strategy_registry,
)


def test_target_decoy_strategy_registry_includes_expected_strategies() -> None:
    registry = build_target_decoy_strategy_registry()

    by_kind = {entry.strategy_kind: entry for entry in registry.entries}
    assert set(by_kind) == {
        TargetDecoyStrategyKind.CONCATENATED,
        TargetDecoyStrategyKind.SEPARATE,
        TargetDecoyStrategyKind.PICKED,
        TargetDecoyStrategyKind.ENTRAPMENT,
        TargetDecoyStrategyKind.CUSTOM,
        TargetDecoyStrategyKind.NO_DECOY,
    }
    assert by_kind[TargetDecoyStrategyKind.NO_DECOY].requires_decoy_channel is False
    assert by_kind[TargetDecoyStrategyKind.PICKED].supports_group is True
    assert len(registry.reproducibility_hash) == 64


def test_target_decoy_strategy_registry_accepts_custom_overrides() -> None:
    custom = TargetDecoyStrategyDefinition(
        strategy_kind=TargetDecoyStrategyKind.CUSTOM,
        display_name="Study-specific custom confidence",
        supports_psm=True,
        supports_peptide=True,
        supports_protein=True,
        supports_ptm=True,
        supports_group=True,
        requires_decoy_channel=False,
        reproducibility_notes=("uses an externally validated empirical bayes model",),
        cautionary_notes=("requires calibration snapshots per run",),
    )
    registry = build_target_decoy_strategy_registry(custom_entries=(custom,))

    custom_entry = next(
        entry
        for entry in registry.entries
        if entry.strategy_kind is TargetDecoyStrategyKind.CUSTOM
    )
    assert custom_entry.display_name == "Study-specific custom confidence"
    assert custom_entry.supports_ptm is True
