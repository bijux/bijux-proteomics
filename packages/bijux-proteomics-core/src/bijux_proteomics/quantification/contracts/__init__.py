# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Focused quantification contracts facade."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.quantification.public_api import (
    CONTRACTS_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    load_public_export,
    module_directory,
)

__all__, _CONTRACTS_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(CONTRACTS_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _CONTRACTS_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
