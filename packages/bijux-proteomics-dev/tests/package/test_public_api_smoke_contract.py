# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    load_public_package_apis as load_governed_public_package_apis,
)
from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    ordered_public_package_modules as ordered_governed_public_package_modules,
)

from .public_api_smoke_support import load_public_package_apis
from .public_api_smoke_support import ordered_public_package_modules


def test_public_api_smoke_support_matches_governed_package_order() -> None:
    assert ordered_public_package_modules() == ordered_governed_public_package_modules()


def test_public_api_smoke_support_matches_governed_root_export_loads() -> None:
    support_loads = load_public_package_apis()
    governed_loads = load_governed_public_package_apis()

    assert tuple(
        (load.package_name, load.module_name, load.export_names) for load in support_loads
    ) == tuple(
        (load.package_name, load.module_name, load.export_names)
        for load in governed_loads
    )
