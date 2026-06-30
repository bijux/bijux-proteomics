"""Workflow artifact export and governed result-bundle owners."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.facade_export_catalog import (
    EXPORT_FACADE_OWNERS,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    load_public_export,
    module_directory,
    ordered_facade_owners,
)

__all__, _EXPORT_INDEX = build_lazy_export_index(
    ordered_facade_owners(EXPORT_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
