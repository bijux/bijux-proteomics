# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing diagnosis and action surfaces."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.lab.public_api import (
    LAB_ROOT_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    load_public_export,
    module_directory,
)

__all__, _LAB_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(LAB_ROOT_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _LAB_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
