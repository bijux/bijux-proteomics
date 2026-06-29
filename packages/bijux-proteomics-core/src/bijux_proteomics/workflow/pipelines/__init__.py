"""Workflow orchestration pipelines composed from domain-owned scientific engines."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.public_api import (
    PIPELINE_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    load_public_export,
    module_directory,
)

__all__, _PIPELINE_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(PIPELINE_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _PIPELINE_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
