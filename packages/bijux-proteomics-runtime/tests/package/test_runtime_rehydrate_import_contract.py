# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_rehydrate_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.rehydrate")

    assert module.load_completed_run is not None
