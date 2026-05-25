from __future__ import annotations

from bijux_proteomics_runtime.support.primitives.api_lock import (
    CORE_API_FROZEN,
    DEPRECATED_EXTENSIONS,
    DO_NOT_EXTEND_ZONES,
)
from bijux_proteomics_runtime.support.primitives.stability import (
    STABILITY_EXPECTATIONS,
    StabilityLevel,
)


def test_runtime_stability_marks_canonical_public_modules_stable() -> None:
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.api"] == StabilityLevel.STABLE
    )


def test_runtime_stability_marks_runtime_owned_zones() -> None:
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.artifacts"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.providers"]
        == StabilityLevel.EXPERIMENTAL
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.providers.remote"]
        == StabilityLevel.EXPERIMENTAL
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.execution"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.resume"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.runs"] == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.state"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.support"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.workflows"]
        == StabilityLevel.SEALED
    )


def test_runtime_api_lock_freezes_canonical_runtime_symbols() -> None:
    assert "bijux_proteomics_runtime.runs.RunManager" in CORE_API_FROZEN
    assert "bijux_proteomics_runtime.runs.RunConfig" in CORE_API_FROZEN
    assert "bijux_proteomics_runtime.api.cli.cli" in CORE_API_FROZEN


def test_runtime_api_lock_declares_runtime_owned_extension_boundaries() -> None:
    assert "bijux_proteomics_runtime.providers.remote" in DEPRECATED_EXTENSIONS
    assert "bijux_proteomics_runtime.artifacts" in DO_NOT_EXTEND_ZONES
    assert "bijux_proteomics_runtime.resume" in DO_NOT_EXTEND_ZONES
    assert "bijux_proteomics_runtime.runs" in DO_NOT_EXTEND_ZONES
    assert "bijux_proteomics_runtime.state" in DO_NOT_EXTEND_ZONES
    assert "bijux_proteomics_runtime.support" in DO_NOT_EXTEND_ZONES
    assert "bijux_proteomics_runtime.workflows" in DO_NOT_EXTEND_ZONES
