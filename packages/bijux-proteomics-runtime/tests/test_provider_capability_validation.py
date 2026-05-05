# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_runtime.providers import factory
from bijux_proteomics_runtime.runtime.control import (
    provider_capabilities as capabilities,
)
from bijux_proteomics_runtime.runtime.control.provider_capabilities import (
    validate_runtime_capabilities,
)


def test_capabilities_auto_requires_gpu_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "cuda_available", lambda: False)
    monkeypatch.setattr(
        capabilities, "provider_requirements", lambda _provider_name: []
    )
    config = {
        "predictors_enabled": ["local_esmfold"],
        "resource_limits": {"gpu_seconds": 0.0},
        "execution_mode": "auto",
        "require_human_decision": True,
    }
    errors, warnings = validate_runtime_capabilities(config)
    assert "gpu_required" in errors
    assert not warnings


def test_capabilities_cpu_mode_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "cuda_available", lambda: False)
    monkeypatch.setattr(
        capabilities, "provider_requirements", lambda _provider_name: []
    )
    config = {
        "predictors_enabled": ["local_esmfold"],
        "resource_limits": {"gpu_seconds": 0.0},
        "execution_mode": "cpu",
        "require_human_decision": True,
    }
    errors, warnings = validate_runtime_capabilities(config)
    assert not errors
    assert "cpu_mode:local_esmfold" in warnings
