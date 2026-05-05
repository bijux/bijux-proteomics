# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Catalog of runtime execution agents."""

from __future__ import annotations

from typing import Any


class AgentCatalog:
    """Mutable runtime catalog for agent classes used during execution."""

    _entries: dict[str, type[Any]] = {}
    _locked: bool = False

    @classmethod
    def list(cls) -> tuple[type[Any], ...]:
        return tuple(cls._entries.values())

    @classmethod
    def lock(cls) -> None:
        cls._locked = True

    @classmethod
    def clear(cls) -> None:
        cls._entries.clear()
        cls._locked = False

    @classmethod
    def register(cls, agent_class: type[Any]) -> None:
        if cls._locked:
            raise ValueError("AgentCatalog is locked.")
        name = agent_class.name
        if name in cls._entries:
            raise ValueError(f"Agent already registered: {name}")
        cls._entries[name] = agent_class

    @classmethod
    def get(cls, name: str) -> type[Any]:
        return cls._entries[name]


__all__ = ["AgentCatalog"]
