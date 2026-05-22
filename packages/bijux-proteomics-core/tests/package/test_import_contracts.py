# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_core_package_import_contract() -> None:
    package = importlib.import_module("bijux_proteomics")

    assert package.__name__ == "bijux_proteomics"


def test_core_cli_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.interfaces.cli")

    assert module.cli is not None
