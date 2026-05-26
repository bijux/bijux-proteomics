# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider capability gates for runtime execution."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    provider_requirements,
)
from bijux_proteomics_runtime.providers.contracts import ProviderCapabilities
from bijux_proteomics_runtime.providers.selection import cuda_available

KNOWN_PROVIDERS = frozenset(
    {
        "heuristic_proxy",
        "local_esmfold",
        "local_rosettafold",
        "api_colabfold",
        "api_openprotein_esmfold",
        "api_openprotein_alphafold",
    }
)


def evaluate_runtime_capabilities(
    config: Mapping[str, object],
    *,
    known_providers: set[str] | frozenset[str],
    provider_capabilities: Mapping[str, ProviderCapabilities],
    cuda_probe: Callable[[], bool],
    requirements_lookup: Callable[[str], list[str]],
    allow_unknown: bool = False,
) -> tuple[list[str], list[str]]:
    """Return runtime capability errors and warnings for one config."""
    errors: list[str] = []
    warnings: list[str] = []
    enabled_obj = config.get("predictors_enabled", []) or []
    enabled = enabled_obj if isinstance(enabled_obj, list) else []
    if not enabled:
        return ["no_providers_enabled"], warnings
    execution_mode_obj = config.get("execution_mode", "auto")
    execution_mode = (
        execution_mode_obj if isinstance(execution_mode_obj, str) else "auto"
    ).lower()
    for provider_name in enabled:
        if provider_name not in known_providers and not allow_unknown:
            errors.append(f"unknown_provider:{provider_name}")
            continue
        capabilities = provider_capabilities.get(provider_name)
        if capabilities:
            gpu_ok = cuda_probe()
            resource_limits_obj = config.get("resource_limits", {})
            resource_limits = (
                resource_limits_obj if isinstance(resource_limits_obj, dict) else {}
            )
            gpu_seconds = float(resource_limits.get("gpu_seconds", 0.0))
            if execution_mode == "gpu":
                if not gpu_ok:
                    errors.append("gpu_required")
                elif not capabilities.supports_gpu:
                    errors.append("provider_gpu_unsupported")
            elif execution_mode == "cpu":
                if not capabilities.supports_cpu:
                    errors.append("provider_cpu_unsupported")
                else:
                    warnings.append(f"cpu_mode:{provider_name}")
            else:
                if gpu_ok:
                    if not capabilities.supports_gpu:
                        errors.append("provider_gpu_unsupported")
                else:
                    if gpu_seconds <= 0.0 and capabilities.supports_gpu:
                        errors.append("gpu_required")
                    elif (
                        capabilities.supports_cpu and capabilities.cpu_fallback_allowed
                    ):
                        warnings.append(f"cpu_fallback:{provider_name}")
                    else:
                        errors.append("gpu_required")
        errors.extend(requirements_lookup(provider_name))
    return errors, warnings


def validate_runtime_capabilities(
    config: Mapping[str, object], allow_unknown: bool = False
) -> tuple[list[str], list[str]]:
    """Return runtime capability errors and warnings for one config."""
    return evaluate_runtime_capabilities(
        config,
        known_providers=KNOWN_PROVIDERS,
        provider_capabilities=PROVIDER_CAPABILITIES,
        cuda_probe=cuda_available,
        requirements_lookup=provider_requirements,
        allow_unknown=allow_unknown,
    )


__all__ = [
    "KNOWN_PROVIDERS",
    "PROVIDER_CAPABILITIES",
    "evaluate_runtime_capabilities",
    "provider_requirements",
    "validate_runtime_capabilities",
]
