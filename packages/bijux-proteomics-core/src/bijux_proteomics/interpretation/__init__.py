# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biological interpretation and downstream annotation surfaces."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.interpretation.public_api import (
    INTERPRETATION_ROOT_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    module_directory,
    resolve_public_export,
)

__all__, _INTERPRETATION_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(INTERPRETATION_ROOT_FACADE_OWNERS),
    collision_policy="prefer_first_owner",
)


def __getattr__(name: str) -> Any:
    return resolve_public_export(
        __name__, globals(), _INTERPRETATION_EXPORT_INDEX, name
    )


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
