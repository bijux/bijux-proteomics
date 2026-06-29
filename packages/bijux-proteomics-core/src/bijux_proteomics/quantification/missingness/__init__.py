# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantification missingness and readiness owners."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.quantification.public_api import (
    MISSINGNESS_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    load_public_export,
    module_directory,
)

__all__, _MISSINGNESS_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(MISSINGNESS_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _MISSINGNESS_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
