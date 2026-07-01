# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""External engine import and adapter-family identification owners."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.identification._facade_runtime import (
    build_facade_dir,
    resolve_facade_export,
)
from bijux_proteomics.identification.public_api import (
    build_facade_export_map,
    flatten_facade_exports,
    list_identification_adapter_api_modules,
)

_ADAPTER_API_MODULES = list_identification_adapter_api_modules()
_ADAPTER_EXPORT_OWNER_MAP = build_facade_export_map(_ADAPTER_API_MODULES)
_ADAPTER_PUBLIC_EXPORTS = flatten_facade_exports(_ADAPTER_API_MODULES)

__all__ = list(_ADAPTER_PUBLIC_EXPORTS)


def __getattr__(name: str) -> Any:
    return resolve_facade_export(name, _ADAPTER_EXPORT_OWNER_MAP, globals())


def __dir__() -> list[str]:
    return build_facade_dir(globals(), _ADAPTER_PUBLIC_EXPORTS)
