# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Cost tracking helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CostSummary:
    """CostSummary."""

    totals: dict[str, float] = field(default_factory=dict)

    def add(self, name: str, value: float) -> None:
        """add."""
        self.totals[name] = self.totals.get(name, 0.0) + float(value)

    def get(self, name: str) -> float:
        """get."""
        return float(self.totals.get(name, 0.0))
