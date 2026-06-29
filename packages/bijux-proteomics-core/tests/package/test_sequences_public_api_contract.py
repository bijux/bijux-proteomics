# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import sequences
from bijux_proteomics.sequences.public_api import (
    SEQUENCES_FACADE_BUDGET,
    SEQUENCES_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)


def test_sequences_facade_ledger_fits_surface_budget() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(SEQUENCES_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert len(export_names) <= SEQUENCES_FACADE_BUDGET.max_public_symbols, (
        f"sequence facade exports {len(export_names)} symbols, "
        f"exceeding its budget of {SEQUENCES_FACADE_BUDGET.max_public_symbols}"
    )


def test_sequences_facade_ledger_keeps_export_names_unambiguous() -> None:
    export_names, owner_map = build_lazy_export_index(
        facade_owner_modules(SEQUENCES_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert len(export_names) == len(set(export_names))
    assert set(export_names) == set(owner_map)


def test_sequences_facade_ledger_preserves_representative_exports() -> None:
    export_names, _ = build_lazy_export_index(
        facade_owner_modules(SEQUENCES_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert "parse_fasta_document" in export_names
    assert "build_protein_index" in export_names
    assert "build_protein_identity_resolution_report" in export_names
    assert "build_theoretical_digest_bundle" in export_names
    assert "render_peptide_detectability_tsv" in export_names


def test_sequences_root_runtime_exports_match_governed_owner_ledger() -> None:
    expected_exports, _ = build_lazy_export_index(
        facade_owner_modules(SEQUENCES_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert tuple(sequences.__all__) == expected_exports
    assert "Path" not in sequences.__all__
    assert "ConfigDict" not in sequences.__all__


def test_sequences_root_facade_init_stays_within_budget() -> None:
    init_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "bijux_proteomics"
        / "sequences"
        / "__init__.py"
    )

    assert (
        sum(1 for _ in init_path.open(encoding="utf-8"))
        <= SEQUENCES_FACADE_BUDGET.max_init_lines
    )
