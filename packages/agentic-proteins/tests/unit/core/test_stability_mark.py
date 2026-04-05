# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import sys
import types

from agentic_proteins.core.stability import StabilityLevel


def test_stability_mark_sets_module_attribute() -> None:
    module = types.ModuleType("temp_stability_module")
    sys.modules["temp_stability_module"] = module
    exec("from agentic_proteins.core.stability import stable\nstable()", module.__dict__)
    assert module.__stability__ == StabilityLevel.STABLE
