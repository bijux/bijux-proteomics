# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import sys
from types import ModuleType
from typing import cast
import warnings

from bijux_proteomics_foundation.compatibility import (
    ImportMigrationSurface,
    compatibility_export_names,
    compatibility_module_dir,
    compatibility_module_getattr,
    emit_compatibility_import_warning,
    import_migration_deprecation_message,
)


def test_import_migration_surface_forwards_exports_and_dir() -> None:
    class _FakeImportMigrationModule(ModuleType):
        __all__: tuple[str, str]
        alpha: object
        beta: object

    module_name = "_bijux_import_migration_surface_module"
    fake_module = cast(_FakeImportMigrationModule, ModuleType(module_name))
    fake_module.__all__ = ("alpha", "beta")
    fake_module.alpha = object()
    fake_module.beta = object()
    sys.modules[module_name] = fake_module
    surface = ImportMigrationSurface(
        legacy_import_path="legacy.alpha",
        canonical_import_path=module_name,
        retirement_condition="retire when callers import the canonical module directly",
        rationale="test surface",
    )
    try:
        assert compatibility_export_names(surface) == ("alpha", "beta")
        assert compatibility_module_getattr(surface, "alpha") is fake_module.alpha
        assert "alpha" in compatibility_module_dir({}, surface)
        assert "beta" in compatibility_module_dir({}, surface)
    finally:
        sys.modules.pop(module_name, None)


def test_import_migration_surface_emits_deprecation_warning_with_canonical_target() -> (
    None
):
    surface = ImportMigrationSurface(
        legacy_import_path="bijux_proteomics.tabular",
        canonical_import_path="bijux_proteomics._tabular",
        retirement_condition="retire when downstream callers stop importing the compatibility path",
        rationale="shared tabular parsing moved behind a private owner",
    )

    assert (
        import_migration_deprecation_message(surface)
        == "bijux_proteomics.tabular is a compatibility import surface; import "
        "bijux_proteomics._tabular instead. retire when downstream callers stop "
        "importing the compatibility path"
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        emit_compatibility_import_warning(surface)

    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert "bijux_proteomics._tabular" in str(caught[0].message)
