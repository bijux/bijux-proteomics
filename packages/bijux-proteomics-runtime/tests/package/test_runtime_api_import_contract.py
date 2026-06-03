# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_api_app_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.api.app")

    assert module.app is not None
