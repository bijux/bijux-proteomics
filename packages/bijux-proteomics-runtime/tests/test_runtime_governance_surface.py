from __future__ import annotations

from bijux_proteomics_runtime.core.stability import STABILITY_EXPECTATIONS, StabilityLevel


def test_runtime_stability_marks_canonical_public_modules_stable() -> None:
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.api"]
        == StabilityLevel.STABLE
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
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.execution"]
        == StabilityLevel.SEALED
    )
    assert (
        STABILITY_EXPECTATIONS["bijux_proteomics_runtime.runtime"]
        == StabilityLevel.SEALED
    )
