# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide chemistry, isotope-labeling, and fragment-reference surfaces."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.chemistry.public_api import (
    CHEMISTRY_ROOT_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    module_directory,
    resolve_public_export,
)

__all__, _CHEMISTRY_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(CHEMISTRY_ROOT_FACADE_OWNERS),
    collision_policy="prefer_first_owner",
)


def __getattr__(name: str) -> Any:
    return resolve_public_export(__name__, globals(), _CHEMISTRY_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
