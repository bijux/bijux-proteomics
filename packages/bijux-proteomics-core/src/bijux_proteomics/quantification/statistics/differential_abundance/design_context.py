# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Design-context resolution for differential abundance analysis."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.design import (
    QuantDesignContrast,
    QuantDesignMatrixReport,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialBrokenPairEntry,
    PairedDifferentialPolicy,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
)
from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy


def require_differential_table_sample_ids(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    sample_run_policy: SampleRunAnalysisPolicy,
) -> None:
    """Require quantification table sample ids to cover the analysis design."""

    missing_sample_ids = tuple(
        sorted(
            {
                entry.sample_id
                for entry in design_entries
                if entry.sample_id not in table.sample_ids
            }
        )
    )
    if not missing_sample_ids:
        return
    raise ValueError(
        "quantification table sample ids do not cover the resolved analysis design "
        f"for sample/run policy {sample_run_policy.value!r}; missing sample ids: "
        + ", ".join(missing_sample_ids)
    )


def sample_ids_for_condition(
    condition_by_sample: dict[str, str],
    condition: str,
) -> tuple[str, ...]:
    """Return the ordered sample ids for one condition label."""

    return tuple(
        sample_id
        for sample_id, sample_condition in condition_by_sample.items()
        if sample_condition == condition
    )


def resolve_design_contrast(
    design_matrix: QuantDesignMatrixReport,
    *,
    condition_a: str,
    condition_b: str,
    contrast_name: str | None = None,
) -> QuantDesignContrast:
    """Resolve one explicit design contrast for differential abundance."""

    if contrast_name is not None:
        for contrast in design_matrix.contrasts:
            if contrast.contrast_name == contrast_name:
                if (
                    contrast.condition_a != condition_a
                    or contrast.condition_b != condition_b
                ):
                    raise ValueError(
                        "design contrast does not match the requested differential conditions"
                    )
                return contrast
        raise ValueError(f"unknown design contrast {contrast_name!r}")
    for contrast in design_matrix.contrasts:
        if contrast.condition_a == condition_a and contrast.condition_b == condition_b:
            return contrast
    raise ValueError("design matrix does not preserve the requested condition contrast")


def resolve_design_pairs(
    design_matrix: QuantDesignMatrixReport,
    *,
    condition_a: str,
    condition_b: str,
    paired_policy: PairedDifferentialPolicy,
) -> tuple[tuple[tuple[str, str, str], ...], tuple[DifferentialBrokenPairEntry, ...]]:
    """Resolve complete and broken pairs for paired differential testing."""

    rows_by_pair_id: dict[str, dict[str, list[str]]] = {}
    broken_pairs: list[DifferentialBrokenPairEntry] = []
    for row in design_matrix.rows:
        if row.condition not in {condition_a, condition_b}:
            continue
        if row.pair_id in (None, ""):
            broken_pairs.append(
                DifferentialBrokenPairEntry(
                    condition_a=condition_a,
                    condition_b=condition_b,
                    pair_id=None,
                    sample_ids_a=(row.sample_id,)
                    if row.condition == condition_a
                    else (),
                    sample_ids_b=(row.sample_id,)
                    if row.condition == condition_b
                    else (),
                    reason_code="missing_pair_id",
                    detail=(
                        f"sample {row.sample_id} in condition {row.condition} is missing "
                        f"{paired_policy.pair_id_field}"
                    ),
                )
            )
            continue
        pair_id = row.pair_id
        if pair_id is None:
            raise RuntimeError("paired differential rows must resolve pair ids")
        by_condition = rows_by_pair_id.setdefault(
            pair_id,
            {condition_a: [], condition_b: []},
        )
        by_condition[row.condition].append(row.sample_id)
    complete_pairs: list[tuple[str, str, str]] = []
    for pair_id, grouped in rows_by_pair_id.items():
        sample_ids_a = tuple(sorted(grouped[condition_a]))
        sample_ids_b = tuple(sorted(grouped[condition_b]))
        if len(sample_ids_a) != 1 or len(sample_ids_b) != 1:
            if not sample_ids_a or not sample_ids_b:
                reason_code = "unmatched_pair"
                detail = (
                    f"pair {pair_id} does not contain exactly one sample in each "
                    f"of {condition_a} and {condition_b}"
                )
            else:
                reason_code = "duplicated_pair_members"
                detail = f"pair {pair_id} contains duplicated samples within at least one condition"
            broken_pairs.append(
                DifferentialBrokenPairEntry(
                    condition_a=condition_a,
                    condition_b=condition_b,
                    pair_id=pair_id,
                    sample_ids_a=sample_ids_a,
                    sample_ids_b=sample_ids_b,
                    reason_code=reason_code,
                    detail=detail,
                )
            )
            continue
        complete_pairs.append((pair_id, sample_ids_a[0], sample_ids_b[0]))
    return tuple(sorted(complete_pairs)), tuple(
        sorted(
            broken_pairs,
            key=lambda entry: (
                entry.pair_id or "",
                entry.reason_code,
                entry.sample_ids_a,
                entry.sample_ids_b,
            ),
        )
    )


__all__ = [
    "require_differential_table_sample_ids",
    "resolve_design_contrast",
    "resolve_design_pairs",
    "sample_ids_for_condition",
]
