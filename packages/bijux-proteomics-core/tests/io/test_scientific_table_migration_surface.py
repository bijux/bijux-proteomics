# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
import warnings

from bijux_proteomics_foundation.compatibility import compatibility_export_names


def test_scientific_table_migration_surface_warns_and_forwards_private_owner() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        public_module = importlib.import_module("bijux_proteomics.scientific_tables")

    private_module = importlib.import_module("bijux_proteomics._scientific_tables")

    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert public_module.__deprecated__ is True
    assert public_module.CANONICAL_IMPORT_PATH == "bijux_proteomics._scientific_tables"
    assert (
        public_module.ScientificTableValidationError
        is private_module.ScientificTableValidationError
    )
    assert public_module.validate_scientific_table is private_module.validate_scientific_table
    assert tuple(public_module.__all__) == compatibility_export_names(
        public_module.MIGRATION_SURFACE
    )
    assert "compatibility import surface" in public_module.DEPRECATION_MESSAGE
