# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_diff_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.diff")

    assert module.diff_completed_runs is not None
