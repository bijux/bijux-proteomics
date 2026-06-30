# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compartment-biology assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyPolicy,
    build_compartment_biology_report,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.biological_context_mapping import (
        BiologicalContextRecord,
    )
    from bijux_proteomics.interpretation.compartment_biology import (
        CompartmentBiologyReport,
    )
    from bijux_proteomics.io.formats import ExperimentalDesignEntry
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.quantification.contracts.differential import (
        DifferentialAbundanceReport,
    )
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )


def _build_biological_compartment_biology_report(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    context_records: tuple[BiologicalContextRecord, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
) -> CompartmentBiologyReport | None:
    if not any(
        record.context_kind is BiologicalContextKind.SUBCELLULAR_COMPARTMENT
        for record in context_records
    ):
        return None

    return build_compartment_biology_report(
        normalized_table,
        differential_report,
        context_records,
        design_entries=design_entries,
        policy=CompartmentBiologyPolicy(
            max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
            min_absolute_log2_fold_change=(
                active_selection_policy.min_absolute_log2_fold_change
            ),
        ),
    )
