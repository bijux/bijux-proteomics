from __future__ import annotations

from bijux_proteomics_dev.governance.foundation.package_boundary_coherence import (
    validate_package_boundary_coherence,
)


def test_package_boundary_coherence_has_no_live_failures() -> None:
    assert validate_package_boundary_coherence() == ()
