"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.providers import factory
from bijux_proteomics_runtime.runtime.control.provider_capabilities import KNOWN_PROVIDERS

PROVIDER_CAPABILITIES = factory.PROVIDER_CAPABILITIES


def cuda_available() -> bool:
    """Read GPU availability through the canonical provider factory."""
    return factory.cuda_available()


def provider_requirements(provider_name: str) -> list[str]:
    """Read provider dependency requirements through the canonical factory."""
    return factory.provider_requirements(provider_name)


def validate_runtime_capabilities(
    config: dict[str, object], allow_unknown: bool = False
) -> tuple[list[str], list[str]]:
    """Validate runtime capability requirements through the compat import path."""
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
        if provider_name not in KNOWN_PROVIDERS and not allow_unknown:
            errors.append(f"unknown_provider:{provider_name}")
            continue
        capabilities = PROVIDER_CAPABILITIES.get(provider_name)
        if capabilities:
            gpu_ok = cuda_available()
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
                    elif capabilities.supports_cpu and capabilities.cpu_fallback_allowed:
                        warnings.append(f"cpu_fallback:{provider_name}")
                    else:
                        errors.append("gpu_required")
        errors.extend(provider_requirements(provider_name))
    return errors, warnings


__all__ = [
    "KNOWN_PROVIDERS",
    "PROVIDER_CAPABILITIES",
    "cuda_available",
    "provider_requirements",
    "validate_runtime_capabilities",
]
