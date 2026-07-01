# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Effect-size-first differential abundance review builders."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceTestType,
    LabelFreeQuantTable,
    PairedDifferentialPolicy,
)
from bijux_proteomics.quantification.provenance.review.models import (
    EffectSizeFirstDaEntry,
    EffectSizeFirstDaReport,
)
from bijux_proteomics.quantification.statistics import (
    build_differential_abundance_report,
)


def build_effect_size_first_differential_abundance_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
) -> EffectSizeFirstDaReport:
    """Build a DA report ranked by effect size with statistical and QC caveats retained."""
    paired_policy = (
        PairedDifferentialPolicy()
        if all(entry.pair_id not in (None, "") for entry in design_entries)
        else None
    )
    da = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        test_type=(
            DifferentialAbundanceTestType.PAIRED_T_TEST
            if paired_policy is not None
            else DifferentialAbundanceTestType.WELCH_T_TEST
        ),
        paired_policy=paired_policy,
    )
    entries: list[EffectSizeFirstDaEntry] = []
    for entry in da.entries:
        caveats: list[str] = []
        if entry.observations_a == 0 or entry.observations_b == 0:
            caveats.append("one condition has no observed replicates for this entity")
        if entry.adjusted_p_value is None:
            caveats.append("adjusted p-value is unavailable")
        if entry.uncertainty_note:
            caveats.append(entry.uncertainty_note)
        if entry.effect_size_cohens_d is None:
            caveats.append("effect size could not be estimated robustly")
        entries.append(
            EffectSizeFirstDaEntry(
                entity_id=entry.entity_id,
                log2_fold_change=entry.log2_fold_change,
                effect_size_cohens_d=entry.effect_size_cohens_d,
                standard_error=entry.standard_error,
                confidence_interval_low=entry.confidence_interval_low,
                confidence_interval_high=entry.confidence_interval_high,
                p_value=entry.p_value,
                adjusted_p_value=entry.adjusted_p_value,
                observations_a=entry.observations_a,
                observations_b=entry.observations_b,
                uncertainty_note=entry.uncertainty_note,
                caveats=tuple(caveats),
            )
        )
    ranked = tuple(
        sorted(
            entries,
            key=lambda item: (
                -(
                    abs(item.effect_size_cohens_d)
                    if item.effect_size_cohens_d is not None
                    else abs(item.log2_fold_change)
                ),
                item.adjusted_p_value if item.adjusted_p_value is not None else 1.0,
                item.entity_id,
            ),
        )
    )
    global_caveats: list[str] = []
    if any(entry.adjusted_p_value is None for entry in ranked):
        global_caveats.append("some entities are missing adjusted p-values")
    if any(entry.observations_a < 2 or entry.observations_b < 2 for entry in ranked):
        global_caveats.append("one or more entities have low replicate support")
    if not global_caveats:
        global_caveats.append(
            "effect-size ranking includes complete statistical annotations"
        )
    return EffectSizeFirstDaReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=ranked,
        global_caveats=tuple(global_caveats),
    )


__all__ = ["build_effect_size_first_differential_abundance_report"]
