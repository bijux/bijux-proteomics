# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import chemistry
from bijux_proteomics.chemistry.public_api import (
    CHEMISTRY_ROOT_FACADE_BUDGET,
    CHEMISTRY_ROOT_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)


def test_chemistry_facade_ledger_fits_surface_budget() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(CHEMISTRY_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert len(export_names) <= CHEMISTRY_ROOT_FACADE_BUDGET.max_public_symbols, (
        f"chemistry facade exports {len(export_names)} symbols, "
        f"exceeding its budget of {CHEMISTRY_ROOT_FACADE_BUDGET.max_public_symbols}"
    )


def test_chemistry_facade_ledger_keeps_export_names_unambiguous() -> None:
    export_names, owner_map = build_lazy_export_index(
        facade_owner_modules(CHEMISTRY_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert len(export_names) == len(set(export_names))
    assert set(export_names) == set(owner_map)


def test_chemistry_facade_ledger_preserves_representative_exports() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(CHEMISTRY_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert "calculate_peptide_mz" in export_names
    assert "predict_peptide_isotope_envelope" in export_names
    assert "load_modification_pack" in export_names
    assert "build_fragment_ion_review_report" in export_names
    assert "validate_theoretical_fragment_reference_cases" in export_names


def test_chemistry_root_runtime_exports_match_governed_owner_ledger() -> None:
    expected_exports, _ = build_lazy_export_index(
        facade_owner_modules(CHEMISTRY_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert tuple(chemistry.__all__) == expected_exports
    assert "_ADDUCT_DELTAS" not in chemistry.__all__
    assert "_TERMINAL_LABEL_TOKENS" not in chemistry.__all__


def test_chemistry_root_facade_init_stays_within_budget() -> None:
    init_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "bijux_proteomics"
        / "chemistry"
        / "__init__.py"
    )

    assert (
        sum(1 for _ in init_path.open(encoding="utf-8"))
        <= CHEMISTRY_ROOT_FACADE_BUDGET.max_init_lines
    )
