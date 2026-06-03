# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
import warnings

from bijux_proteomics_foundation.compatibility import compatibility_export_names


def test_tabular_migration_surface_warns_and_forwards_private_owner() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        public_module = importlib.import_module("bijux_proteomics.tabular")

    private_module = importlib.import_module("bijux_proteomics._tabular")

    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert public_module.__deprecated__ is True
    assert public_module.CANONICAL_IMPORT_PATH == "bijux_proteomics._tabular"
    assert public_module.DelimitedColumnSpec is private_module.DelimitedColumnSpec
    assert public_module.parse_delimited_table is private_module.parse_delimited_table
    assert tuple(public_module.__all__) == compatibility_export_names(
        public_module.MIGRATION_SURFACE
    )
    assert "compatibility import surface" in public_module.DEPRECATION_MESSAGE
