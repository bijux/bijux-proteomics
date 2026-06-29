# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PSM-level identification evidence, diagnostics, and mapper owners."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.identification._facade_runtime import (
    build_facade_dir,
    resolve_facade_export,
)
from bijux_proteomics.identification.public_api import (
    build_facade_export_map,
    flatten_facade_exports,
    list_identification_psm_api_modules,
)

_PSM_API_MODULES = list_identification_psm_api_modules()
_PSM_EXPORT_OWNER_MAP = build_facade_export_map(_PSM_API_MODULES)
_PSM_PUBLIC_EXPORTS = flatten_facade_exports(_PSM_API_MODULES)

__all__ = list(_PSM_PUBLIC_EXPORTS)


def __getattr__(name: str) -> Any:
    return resolve_facade_export(name, _PSM_EXPORT_OWNER_MAP, globals())


def __dir__() -> list[str]:
    return build_facade_dir(globals(), _PSM_PUBLIC_EXPORTS)
