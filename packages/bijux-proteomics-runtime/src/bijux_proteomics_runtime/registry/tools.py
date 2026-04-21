# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Tool registry."""

from __future__ import annotations

from agentic_proteins.core.tooling import ToolContract


class ToolRegistry:
    """ToolRegistry."""

    _registry: dict[tuple[str, str], ToolContract] = {}
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
        """register."""
        if cls._locked:
            raise ValueError("ToolRegistry is locked.")
        key = (contract.tool_name, contract.version)
        if key in cls._registry:
            raise ValueError(f"Tool already registered: {key}")
        cls._registry[key] = contract

    @classmethod
    def get(cls, name: str, version: str) -> ToolContract:
        """get."""
        return cls._registry[(name, version)]
