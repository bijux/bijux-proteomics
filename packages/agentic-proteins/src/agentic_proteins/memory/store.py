# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Memory store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_proteins.memory.schemas import MemoryRecord, MemoryScope


class MemoryStore(ABC):
    """MemoryStore."""

    @abstractmethod
    def write(self, record: MemoryRecord) -> None:
        """Write a memory record."""

    @abstractmethod
    def query(self, scope: MemoryScope, _filters: list[str]) -> list[MemoryRecord]:
        """Query records by scope and structured filters."""

    @abstractmethod
    def snapshot(self) -> list[MemoryRecord]:
        """Return a point-in-time snapshot of memory."""
