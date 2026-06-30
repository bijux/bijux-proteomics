# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Sequence intake and digestion-adjacent surfaces."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.sequences.public_api import (
    SEQUENCES_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    resolve_public_export,
    module_directory,
)

__all__, _SEQUENCE_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(SEQUENCES_FACADE_OWNERS),
    collision_policy="prefer_first_owner",
)


def __getattr__(name: str) -> Any:
    return resolve_public_export(__name__, globals(), _SEQUENCE_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
