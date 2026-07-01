# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted proteomics selection, result import, coelution, QC, and matrix surfaces."""

from __future__ import annotations

from .public_api import (
    TARGETED_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    module_directory,
    resolve_public_export,
)

__all__, _TARGETED_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(TARGETED_FACADE_OWNERS)
)


def __getattr__(name: str) -> object:
    return resolve_public_export(__name__, globals(), _TARGETED_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
