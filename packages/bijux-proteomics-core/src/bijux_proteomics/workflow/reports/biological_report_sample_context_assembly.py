# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sample-context assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
)
from bijux_proteomics.interpretation.tissue_cell_type_context import (
    build_tissue_cell_type_context_report,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.biological_context_mapping import (
        BiologicalContextRecord,
    )
    from bijux_proteomics.interpretation.tissue_cell_type_context import (
        TissueCellTypeContextReport,
    )
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.study import ExperimentDesign


def _build_biological_sample_context_report(
    *,
    normalized_table: LabelFreeQuantTable,
    experiment_design: ExperimentDesign,
    context_records: tuple[BiologicalContextRecord, ...],
) -> TissueCellTypeContextReport | None:
    if not any(
        record.context_kind
        in {
            BiologicalContextKind.TISSUE_MARKER,
            BiologicalContextKind.CELL_TYPE_MARKER,
        }
        for record in context_records
    ):
        return None

    return build_tissue_cell_type_context_report(
        normalized_table,
        experiment_design,
        context_records,
    )
