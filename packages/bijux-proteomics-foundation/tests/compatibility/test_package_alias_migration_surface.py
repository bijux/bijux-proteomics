# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
import warnings


def test_package_alias_migration_surface_warns_and_forwards_private_owner() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        public_module = importlib.import_module("bijux_proteomics_foundation.package_aliases")

    private_module = importlib.import_module("bijux_proteomics_foundation._package_aliases")

    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert public_module.__deprecated__ is True
    assert (
        public_module.CANONICAL_IMPORT_PATH
        == "bijux_proteomics_foundation._package_aliases"
    )
    assert public_module.alias_package_version is private_module.alias_package_version
    assert (
        public_module.dispatch_alias_entrypoint
        is private_module.dispatch_alias_entrypoint
    )
    assert tuple(public_module.__all__) == tuple(private_module.__all__)
    assert "compatibility import surface" in public_module.DEPRECATION_MESSAGE
