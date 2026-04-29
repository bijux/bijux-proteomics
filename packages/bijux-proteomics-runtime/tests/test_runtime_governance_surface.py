from __future__ import annotations

from bijux_proteomics_runtime.core.api_lock import (
    CORE_API_FROZEN,
    DEPRECATED_EXTENSIONS,
    DO_NOT_EXTEND_ZONES,
)
from bijux_proteomics_runtime.core.stability import (
    STABILITY_EXPECTATIONS,
    StabilityLevel,
)


def test_runtime_stability_marks_canonical_public_modules_stable() -> None:
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.api"] == StabilityLevel.STABLE
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.interfaces"]
        == StabilityLevel.STABLE
    )


def test_runtime_stability_marks_runtime_owned_zones() -> None:
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.providers"]
        == StabilityLevel.EXPERIMENTAL
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.providers.experimental"]
        == StabilityLevel.EXPERIMENTAL
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.sandbox"]
        == StabilityLevel.EXPERIMENTAL
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.execution"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.runtime"]
        == StabilityLevel.SEALED
    )


def test_runtime_api_lock_freezes_canonical_runtime_symbols() -> None:
    assert "bijux_proteomics_runtime.runtime.RunManager" in CORE_API_FROZEN
    assert "bijux_proteomics_runtime.runtime.infra.RunConfig" in CORE_API_FROZEN
    assert "bijux_proteomics_runtime.interfaces.cli.cli" in CORE_API_FROZEN


def test_runtime_api_lock_declares_runtime_owned_extension_boundaries() -> None:
    assert "bijux_proteomics_runtime.providers.experimental" in DEPRECATED_EXTENSIONS
    assert "bijux_proteomics_runtime.runtime.control" in DO_NOT_EXTEND_ZONES
    assert "bijux_proteomics_runtime.runtime.infra" in DO_NOT_EXTEND_ZONES
