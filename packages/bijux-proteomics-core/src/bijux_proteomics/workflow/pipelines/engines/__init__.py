"""Workflow engine owners grouped by acquisition and quantification modality."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.facade_pipeline_catalog import (
    ENGINE_PIPELINE_FACADE_OWNERS,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    resolve_public_export,
    module_directory,
    ordered_facade_owners,
)

__all__, _ENGINE_PIPELINE_EXPORT_INDEX = build_lazy_export_index(
    ordered_facade_owners(ENGINE_PIPELINE_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return resolve_public_export(
        __name__,
        globals(),
        _ENGINE_PIPELINE_EXPORT_INDEX,
        name,
    )


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
