# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import agentic_proteins.core.surface_area as surface_area


def test_surface_area_budget() -> None:
    assert (
        len(surface_area.PUBLIC_ENTRYPOINTS)
        <= surface_area.SURFACE_CAPS["public_entrypoints"]
    )
    assert (
        len(surface_area.EXTENSION_POINTS)
        <= surface_area.SURFACE_CAPS["extension_points"]
    )
    assert (
        len(surface_area.CONFIG_KNOBS)
        <= surface_area.SURFACE_CAPS["config_knobs"]
    )
