# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import targeted
from bijux_proteomics.targeted.public_api import (
    TARGETED_FACADE_BUDGET,
    TARGETED_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)


def test_targeted_facade_ledger_fits_surface_budget() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(TARGETED_FACADE_OWNERS)
    )

    assert len(export_names) <= TARGETED_FACADE_BUDGET.max_public_symbols, (
        f"targeted facade exports {len(export_names)} symbols, "
        f"exceeding its budget of {TARGETED_FACADE_BUDGET.max_public_symbols}"
    )


def test_targeted_facade_ledger_keeps_export_names_unambiguous() -> None:
    export_names, owner_map = build_lazy_export_index(
        facade_owner_modules(TARGETED_FACADE_OWNERS)
    )

    assert len(export_names) == len(set(export_names))
    assert set(export_names) == set(owner_map)


def test_targeted_facade_ledger_preserves_representative_exports() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(TARGETED_FACADE_OWNERS)
    )

    assert "build_targeted_assay_qc_report" in export_names
    assert "build_targeted_result_validation_report" in export_names
    assert "build_targeted_transition_selection_report" in export_names
    assert "render_targeted_matrix_missingness_tsv" in export_names
    assert "render_validation_evidence_card_warning_tsv" in export_names


def test_targeted_root_runtime_exports_match_governed_owner_ledger() -> None:
    expected_exports, _ = build_lazy_export_index(
        facade_owner_modules(TARGETED_FACADE_OWNERS)
    )

    assert tuple(targeted.__all__) == expected_exports
    assert "Path" not in targeted.__all__
    assert "ConfigDict" not in targeted.__all__


def test_targeted_root_facade_init_stays_within_budget() -> None:
    init_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "bijux_proteomics"
        / "targeted"
        / "__init__.py"
    )

    assert (
        sum(1 for _ in init_path.open(encoding="utf-8"))
        <= TARGETED_FACADE_BUDGET.max_init_lines
    )
