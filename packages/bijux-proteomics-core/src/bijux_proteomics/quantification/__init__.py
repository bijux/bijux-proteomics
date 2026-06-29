# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Quantification matrices, provenance, and review-bundle surfaces."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.quantification.public_api import (
    QUANTIFICATION_ROOT_FACADE_OWNERS,
    QUANTIFICATION_ROOT_SUBMODULES,
    build_lazy_export_index,
    facade_owner_modules,
    load_public_export,
    load_public_submodule,
    module_directory,
)

__all__, _QUANTIFICATION_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(QUANTIFICATION_ROOT_FACADE_OWNERS),
    collision_policy="prefer_first_owner",
)


def __getattr__(name: str) -> Any:
    if name in QUANTIFICATION_ROOT_SUBMODULES:
        return load_public_submodule(
            __name__,
            globals(),
            QUANTIFICATION_ROOT_SUBMODULES,
            name,
        )
    return load_public_export(__name__, globals(), _QUANTIFICATION_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(
        globals(),
        __all__,
        submodule_names=tuple(QUANTIFICATION_ROOT_SUBMODULES),
    )
