# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib

import agentic_proteins.core.api_lock as api_lock
import agentic_proteins.runtime.control.execution as runtime_execution


def test_core_api_lock_points_to_real_symbols() -> None:
    assert hasattr(runtime_execution, "RunManager")
    for dotted in api_lock.CORE_API_FROZEN:
        module_path, name = dotted.rsplit(".", 1)
        module = importlib.import_module(module_path)
        assert hasattr(module, name)


def test_do_not_extend_zones_declared() -> None:
    assert api_lock.DO_NOT_EXTEND_ZONES
