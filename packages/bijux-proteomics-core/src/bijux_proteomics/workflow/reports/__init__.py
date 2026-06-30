"""Workflow report owners for governed biological and scientific result outputs."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.public_api import (
    REPORT_FACADE_OWNERS,
    build_lazy_export_index,
    load_public_export,
    module_directory,
    ordered_facade_owners,
)

__all__, _REPORT_EXPORT_INDEX = build_lazy_export_index(
    ordered_facade_owners(REPORT_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _REPORT_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
