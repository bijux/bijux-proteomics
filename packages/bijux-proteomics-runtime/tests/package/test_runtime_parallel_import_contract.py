# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_parallel_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.parallel")

    assert module.ParallelStep is not None
    assert module.ParallelRunReport is not None
    assert module.run_parallel_steps is not None
