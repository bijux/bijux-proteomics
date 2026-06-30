"""Workflow orchestration pipelines composed from domain-owned scientific engines."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.facade_pipeline_catalog import (
    PIPELINE_ROOT_OWNERS,
    PIPELINE_SUBMODULES,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    load_public_export,
    load_public_submodule,
    module_directory,
    ordered_facade_owners,
)

__all__, _PIPELINE_EXPORT_INDEX = build_lazy_export_index(
    ordered_facade_owners(PIPELINE_ROOT_OWNERS)
)


def __getattr__(name: str) -> Any:
    if name in PIPELINE_SUBMODULES:
        return load_public_submodule(
            __name__,
            globals(),
            PIPELINE_SUBMODULES,
            name,
        )
    return load_public_export(__name__, globals(), _PIPELINE_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(
        globals(),
        __all__,
        submodule_names=tuple(PIPELINE_SUBMODULES),
    )
