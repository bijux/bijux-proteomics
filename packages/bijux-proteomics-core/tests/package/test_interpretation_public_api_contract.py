# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import interpretation
from bijux_proteomics.interpretation.public_api import (
    INTERPRETATION_ROOT_FACADE_BUDGET,
    INTERPRETATION_ROOT_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)


def test_interpretation_facade_ledger_fits_surface_budget() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(INTERPRETATION_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert len(export_names) <= INTERPRETATION_ROOT_FACADE_BUDGET.max_public_symbols, (
        f"interpretation facade exports {len(export_names)} symbols, "
        "exceeding its budget of "
        f"{INTERPRETATION_ROOT_FACADE_BUDGET.max_public_symbols}"
    )


def test_interpretation_facade_ledger_keeps_export_names_unique() -> None:
    export_names, owner_map = build_lazy_export_index(
        facade_owner_modules(INTERPRETATION_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert len(export_names) == len(set(export_names))
    assert set(export_names) == set(owner_map)


def test_interpretation_facade_ledger_preserves_representative_exports() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(INTERPRETATION_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert "parse_protein_reference_table" in export_names
    assert "build_pathway_activity_report" in export_names
    assert "build_regulator_inference_report" in export_names
    assert "load_annotation_pack" in export_names
    assert "render_tissue_cell_type_interpretation_tsv" in export_names


def test_interpretation_root_runtime_exports_match_governed_owner_ledger() -> None:
    expected_exports, _ = build_lazy_export_index(
        facade_owner_modules(INTERPRETATION_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert tuple(interpretation.__all__) == expected_exports


def test_interpretation_root_facade_init_stays_within_budget() -> None:
    init_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "bijux_proteomics"
        / "interpretation"
        / "__init__.py"
    )

    assert (
        sum(1 for _ in init_path.open(encoding="utf-8"))
        <= INTERPRETATION_ROOT_FACADE_BUDGET.max_init_lines
    )
