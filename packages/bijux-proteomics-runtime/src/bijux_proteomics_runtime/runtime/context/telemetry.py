# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime telemetry collection for one execution run."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time

from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


@dataclass
class TelemetrySample:
    """One named telemetry sample."""

    name: str
    value: float


@dataclass
class TelemetryClient:
    """Collect counters, timers, gauges, and cost for one runtime run."""

    run_id: str
    metrics_path: Path
    counters: dict[str, float] = field(default_factory=dict)
    timers: dict[str, list[float]] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    cost: dict[str, float] = field(default_factory=dict)

    def increment(self, name: str, value: float = 1.0) -> None:
        self.counters[name] = self.counters.get(name, 0.0) + value

    def observe(self, name: str, value: float) -> None:
        self.timers.setdefault(name, []).append(value)

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def record_event(self, name: str) -> None:
        self.events.append(name)

    def add_cost(self, name: str, value: float) -> None:
        self.cost[name] = self.cost.get(name, 0.0) + value

    def observe_time(self, name: str, start_time: float) -> None:
        self.observe(name, (time.time() - start_time) * 1000.0)

    def add_carbon(self, energy_kwh: float, co2_kg: float) -> None:
        self.cost["energy_kwh"] = self.cost.get("energy_kwh", 0.0) + energy_kwh
        self.cost["co2_kg"] = self.cost.get("co2_kg", 0.0) + co2_kg

    def _validate_required(self) -> None:
        required_events = {"run_start"}
        required_timers = {"run_total_ms"}
        required_cost = {"tool_units", "cpu_seconds", "gpu_seconds"}
        missing_events = required_events - set(self.events)
        missing_timers = required_timers - set(self.timers.keys())
        missing_cost = required_cost - set(self.cost.keys())
        missing = sorted(missing_events | missing_timers | missing_cost)
        if missing:
            raise ValueError(f"Missing telemetry fields: {missing}")

    def flush(self) -> None:
        self._validate_required()
        payload = {
            "run_id": self.run_id,
            "counters": self.counters,
            "timers": self.timers,
            "gauges": self.gauges,
            "events": self.events,
            "event_count": len(self.events),
            "cost": self.cost,
        }
        write_json_atomic(self.metrics_path, payload)


__all__ = ["TelemetryClient", "TelemetrySample"]
