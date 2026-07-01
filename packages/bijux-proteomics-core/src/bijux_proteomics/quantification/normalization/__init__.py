# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantification normalization and imputation owners."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.quantification.public_api import (
    NORMALIZATION_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    module_directory,
    resolve_public_export,
)

__all__, _NORMALIZATION_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(NORMALIZATION_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return resolve_public_export(__name__, globals(), _NORMALIZATION_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
