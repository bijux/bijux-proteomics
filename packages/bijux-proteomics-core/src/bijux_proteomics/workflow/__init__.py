"""Scientific workflow blueprints, planning, and runtime reports."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.facade_root_catalog import (
    WORKFLOW_ROOT_OWNERS,
    WORKFLOW_ROOT_SUBMODULES,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    module_directory,
    ordered_facade_owners,
    resolve_public_export,
    resolve_public_submodule,
)

__all__, _WORKFLOW_EXPORT_INDEX = build_lazy_export_index(
    ordered_facade_owners(WORKFLOW_ROOT_OWNERS)
)


def __getattr__(name: str) -> Any:
    if name in WORKFLOW_ROOT_SUBMODULES:
        return resolve_public_submodule(
            __name__,
            globals(),
            WORKFLOW_ROOT_SUBMODULES,
            name,
        )
    return resolve_public_export(__name__, globals(), _WORKFLOW_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(
        globals(),
        __all__,
        submodule_names=tuple(WORKFLOW_ROOT_SUBMODULES),
    )
