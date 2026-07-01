# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Identification evidence, confidence, and search-adapter surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics.identification._facade_runtime import build_facade_dir
from bijux_proteomics.identification.public_api import (
    IDENTIFICATION_ROOT_SUBMODULES,
    build_identification_root_export_owner_map,
    list_identification_root_export_names,
)

_IDENTIFICATION_EXPORT_OWNER_MAP = build_identification_root_export_owner_map()
_IDENTIFICATION_PUBLIC_EXPORTS = list_identification_root_export_names()

__all__ = list(_IDENTIFICATION_PUBLIC_EXPORTS) + list(IDENTIFICATION_ROOT_SUBMODULES)


def __getattr__(name: str) -> Any:
    submodule_path = IDENTIFICATION_ROOT_SUBMODULES.get(name)
    if submodule_path is not None:
        module = import_module(submodule_path)
        globals()[name] = module
        return module
    owner_module = _IDENTIFICATION_EXPORT_OWNER_MAP.get(name)
    if owner_module is not None:
        module = import_module(owner_module)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return build_facade_dir(globals(), tuple(__all__))
