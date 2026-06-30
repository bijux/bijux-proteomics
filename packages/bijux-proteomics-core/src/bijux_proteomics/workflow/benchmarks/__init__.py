"""Benchmark workflow owners for public datasets and quant-truth fixtures."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.workflow.facade_benchmark_catalog import (
    BENCHMARK_FACADE_OWNERS,
    BENCHMARK_SUBMODULES,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    load_public_export,
    load_public_submodule,
    module_directory,
    ordered_facade_owners,
)

__all__, _BENCHMARK_EXPORT_INDEX = build_lazy_export_index(
    ordered_facade_owners(BENCHMARK_FACADE_OWNERS)
)


def __getattr__(name: str) -> Any:
    if name in BENCHMARK_SUBMODULES:
        return load_public_submodule(
            __name__,
            globals(),
            BENCHMARK_SUBMODULES,
            name,
        )
    return load_public_export(__name__, globals(), _BENCHMARK_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(
        globals(),
        __all__,
        submodule_names=tuple(BENCHMARK_SUBMODULES),
    )
