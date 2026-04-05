# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime capability gates for providers and resources."""

from __future__ import annotations

from agentic_proteins.providers.factory import (
    PROVIDER_CAPABILITIES,
    cuda_available,
    provider_requirements,
)

KNOWN_PROVIDERS = {
    "heuristic_proxy",
    "local_esmfold",
    "local_rosettafold",
    "api_colabfold",
    "api_openprotein_esmfold",
    "api_openprotein_alphafold",
}


def validate_runtime_capabilities(
    config: dict, allow_unknown: bool = False
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for capability checks."""
    errors: list[str] = []
    warnings: list[str] = []
    enabled = config.get("predictors_enabled", []) or []
    if not enabled:
        return ["no_providers_enabled"], warnings
    execution_mode = (config.get("execution_mode") or "auto").lower()
    for provider_name in enabled:
        if provider_name not in KNOWN_PROVIDERS and not allow_unknown:
            errors.append(f"unknown_provider:{provider_name}")
            continue
        capabilities = PROVIDER_CAPABILITIES.get(provider_name)
        if capabilities:
            gpu_ok = cuda_available()
            resource_limits = config.get("resource_limits", {})
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
        errors.extend(provider_requirements(provider_name))
    return errors, warnings
