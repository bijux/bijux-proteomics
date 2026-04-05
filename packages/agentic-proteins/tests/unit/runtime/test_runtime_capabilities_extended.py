# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_proteins.runtime.infra import capabilities as capabilities_module


def test_validate_runtime_capabilities_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capabilities_module, "provider_requirements", lambda *_: [])
    monkeypatch.setattr(capabilities_module, "cuda_available", lambda: False)
    errors, warnings = capabilities_module.validate_runtime_capabilities({})
    assert errors == ["no_providers_enabled"]
    errors, _warnings = capabilities_module.validate_runtime_capabilities(
        {"predictors_enabled": ["unknown"]}, allow_unknown=False
    )
    assert "unknown_provider:unknown" in errors
    errors, warnings = capabilities_module.validate_runtime_capabilities(
        {
            "predictors_enabled": ["local_esmfold"],
            "execution_mode": "gpu",
            "resource_limits": {"gpu_seconds": 0.0},
        }
    )
    assert "gpu_required" in errors
    errors, warnings = capabilities_module.validate_runtime_capabilities(
        {
            "predictors_enabled": ["local_rosettafold"],
            "execution_mode": "cpu",
        }
    )
    assert "provider_cpu_unsupported" in errors
    errors, warnings = capabilities_module.validate_runtime_capabilities(
        {
            "predictors_enabled": ["local_esmfold"],
            "execution_mode": "auto",
            "resource_limits": {"gpu_seconds": 0.0},
        }
    )
    assert "gpu_required" in errors or "cpu_fallback:local_esmfold" in warnings
