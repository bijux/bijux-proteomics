# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Catalog of runtime execution tools."""

from __future__ import annotations

from bijux_proteomics_runtime.core.tooling import ToolContract


class ToolCatalog:
    """Mutable runtime catalog for tool contracts used during execution."""

    _registry: dict[tuple[str, str], ToolContract] = {}
    _entries = _registry
    _locked: bool = False

    @classmethod
    def list(cls) -> tuple[ToolContract, ...]:
        return tuple(cls._registry.values())

    @classmethod
    def lock(cls) -> None:
        cls._locked = True

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()
        cls._locked = False

    @classmethod
    def register(cls, contract: ToolContract) -> None:
        if cls._locked:
            raise ValueError("ToolCatalog is locked.")
        key = (contract.tool_name, contract.version)
        if key in cls._registry:
            raise ValueError(f"Tool already registered: {key}")
        cls._registry[key] = contract

    @classmethod
    def get(cls, name: str, version: str) -> ToolContract:
        return cls._registry[(name, version)]


__all__ = ["ToolCatalog"]
