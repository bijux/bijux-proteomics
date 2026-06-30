"""Public benchmark dataset owners for descriptors and governed subsets."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.public_api import (
    BENCHMARK_DATASET_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    load_public_export,
    module_directory,
)

__all__, _BENCHMARK_DATASET_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(BENCHMARK_DATASET_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    return load_public_export(__name__, globals(), _BENCHMARK_DATASET_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
