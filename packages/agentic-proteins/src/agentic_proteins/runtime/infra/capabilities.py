"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.providers import factory
from bijux_proteomics_runtime.runtime.control.provider_capabilities import (
    KNOWN_PROVIDERS,
    evaluate_runtime_capabilities,
)

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
    "cuda_available",
    "provider_requirements",
    "validate_runtime_capabilities",
]
