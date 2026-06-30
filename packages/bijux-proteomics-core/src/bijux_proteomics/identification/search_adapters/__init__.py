# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Search-engine adapter contracts over normalized PSM parsing."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.identification._facade_runtime import (
    build_facade_dir,
    resolve_facade_export,
)
from bijux_proteomics.identification.search_adapters.public_api import (
    build_search_adapter_export_owner_map,
    list_search_adapter_export_names,
)

_SEARCH_ADAPTER_EXPORT_OWNER_MAP = build_search_adapter_export_owner_map()
_SEARCH_ADAPTER_PUBLIC_EXPORTS = list_search_adapter_export_names()

__all__ = list(_SEARCH_ADAPTER_PUBLIC_EXPORTS)


def __getattr__(name: str) -> Any:
    return resolve_facade_export(name, _SEARCH_ADAPTER_EXPORT_OWNER_MAP, globals())


def __dir__() -> list[str]:
    return build_facade_dir(globals(), _SEARCH_ADAPTER_PUBLIC_EXPORTS)
