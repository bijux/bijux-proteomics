# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.runtime.infra.capabilities import validate_runtime_capabilities
from agentic_proteins.providers import factory


def test_capabilities_auto_requires_gpu_budget(monkeypatch) -> None:
    monkeypatch.setattr(factory, "cuda_available", lambda: False)
    config = {
        "predictors_enabled": ["local_esmfold"],
        "resource_limits": {"gpu_seconds": 0.0},
        "execution_mode": "auto",
        "require_human_decision": True,
    }
    errors, warnings = validate_runtime_capabilities(config)
    assert "gpu_required" in errors
    assert not warnings


def test_capabilities_cpu_mode_warns(monkeypatch) -> None:
    monkeypatch.setattr(factory, "cuda_available", lambda: False)
    config = {
        "predictors_enabled": ["local_esmfold"],
        "resource_limits": {"gpu_seconds": 0.0},
        "execution_mode": "cpu",
        "require_human_decision": True,
    }
    errors, warnings = validate_runtime_capabilities(config)
    assert not errors
    assert "cpu_mode:local_esmfold" in warnings
