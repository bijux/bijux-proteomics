# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Protocol

from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    PublicPackageApiLoad,
)
from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    load_public_package_apis as load_governed_public_package_apis,
)
from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    ordered_public_package_modules as ordered_governed_public_package_modules,
)

SUPPORT_PATH = Path(__file__).with_name("public_api_smoke_support.py")


class _PublicApiSmokeSupport(Protocol):
    def load_public_package_apis(self) -> tuple[PublicPackageApiLoad, ...]: ...

    def ordered_public_package_modules(self) -> tuple[tuple[str, str], ...]: ...


def _load_support_module() -> _PublicApiSmokeSupport:
    spec = importlib.util.spec_from_file_location(
        "bijux_proteomics_dev_public_api_smoke_support",
        SUPPORT_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    assert isinstance(module, ModuleType)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SUPPORT = _load_support_module()
load_public_package_apis = _SUPPORT.load_public_package_apis
ordered_public_package_modules = _SUPPORT.ordered_public_package_modules


def test_public_api_smoke_support_matches_governed_package_order() -> None:
    assert ordered_public_package_modules() == ordered_governed_public_package_modules()


def test_public_api_smoke_support_matches_governed_root_export_loads() -> None:
    support_loads = load_public_package_apis()
    governed_loads = load_governed_public_package_apis()

    assert tuple(
        (load.package_name, load.module_name, load.export_names)
        for load in support_loads
    ) == tuple(
        (load.package_name, load.module_name, load.export_names)
        for load in governed_loads
    )
