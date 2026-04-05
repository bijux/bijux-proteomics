from __future__ import annotations

import pytest

from agentic_proteins.providers.base import ProviderCapabilities
from agentic_proteins.runtime.infra import capabilities


def test_validate_runtime_capabilities_unknown_provider() -> None:
    errors, warnings = capabilities.validate_runtime_capabilities(
        {"predictors_enabled": ["unknown"], "execution_mode": "auto"}
    )
    assert "unknown_provider:unknown" in errors
    assert warnings == []


def test_validate_runtime_capabilities_allow_unknown() -> None:
    errors, _warnings = capabilities.validate_runtime_capabilities(
        {"predictors_enabled": ["unknown"]}, allow_unknown=True
    )
    assert errors == []


def test_validate_runtime_capabilities_no_providers() -> None:
    errors, warnings = capabilities.validate_runtime_capabilities({})
    assert errors == ["no_providers_enabled"]
    assert warnings == []


def test_validate_runtime_capabilities_gpu_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(capabilities, "cuda_available", lambda: False)
    monkeypatch.setattr(
        capabilities,
        "PROVIDER_CAPABILITIES",
        {"local_esmfold": ProviderCapabilities(True, True, True)},
    )
    monkeypatch.setattr(capabilities, "provider_requirements", lambda _name: [])
    errors, warnings = capabilities.validate_runtime_capabilities(
        {"predictors_enabled": ["local_esmfold"], "resource_limits": {"gpu_seconds": 0}}
    )
    assert "gpu_required" in errors
    assert warnings == []


def test_validate_runtime_capabilities_cpu_mode_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capabilities, "cuda_available", lambda: True)
    monkeypatch.setattr(
        capabilities,
        "PROVIDER_CAPABILITIES",
        {"local_esmfold": ProviderCapabilities(True, True, True)},
    )
    monkeypatch.setattr(capabilities, "provider_requirements", lambda _name: [])
    errors, warnings = capabilities.validate_runtime_capabilities(
        {"predictors_enabled": ["local_esmfold"], "execution_mode": "cpu"}
    )
    assert errors == []
    assert "cpu_mode:local_esmfold" in warnings


def test_validate_runtime_capabilities_cpu_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capabilities, "cuda_available", lambda: True)
    monkeypatch.setattr(
        capabilities,
        "PROVIDER_CAPABILITIES",
        {"local_esmfold": ProviderCapabilities(True, False, False)},
    )
    monkeypatch.setattr(capabilities, "provider_requirements", lambda _name: [])
    errors, _warnings = capabilities.validate_runtime_capabilities(
        {"predictors_enabled": ["local_esmfold"], "execution_mode": "cpu"}
    )
    assert "provider_cpu_unsupported" in errors


def test_validate_runtime_capabilities_gpu_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capabilities, "cuda_available", lambda: True)
    monkeypatch.setattr(
        capabilities,
        "PROVIDER_CAPABILITIES",
        {"local_esmfold": ProviderCapabilities(False, True, True)},
    )
    monkeypatch.setattr(capabilities, "provider_requirements", lambda _name: [])
    errors, _warnings = capabilities.validate_runtime_capabilities(
        {"predictors_enabled": ["local_esmfold"], "execution_mode": "gpu"}
    )
    assert "provider_gpu_unsupported" in errors
