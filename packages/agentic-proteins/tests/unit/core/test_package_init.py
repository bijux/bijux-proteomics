# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import agentic_proteins as pkg
import agentic_proteins.core as compat_core
import bijux_proteomics_runtime.support.primitives as runtime_primitives


def test_package_exports() -> None:
    assert pkg.__all__ == ["__version__"]
    assert isinstance(pkg.__version__, str)


def test_core_package_forwards_to_runtime_exports() -> None:
    assert compat_core.CostSummary is runtime_primitives.CostSummary
    assert compat_core.FailureType is runtime_primitives.FailureType
    assert compat_core.ExecutionStatus is runtime_primitives.ExecutionStatus
