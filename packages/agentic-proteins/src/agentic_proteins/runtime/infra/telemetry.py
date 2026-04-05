# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Local telemetry client."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time

from agentic_proteins.runtime.workspace import write_json_atomic


@dataclass
class TelemetrySample:
    """TelemetrySample."""

    name: str
    value: float


@dataclass(frozen=True)
class RunTelemetry:
    """RunTelemetry."""

    client: TelemetryClient


@dataclass
class TelemetryClient:
    """TelemetryClient."""

    run_id: str
    metrics_path: Path
    counters: dict[str, float] = field(default_factory=dict)
    timers: dict[str, list[float]] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    cost: dict[str, float] = field(default_factory=dict)

    def increment(self, name: str, value: float = 1.0) -> None:
        """increment."""
        self.counters[name] = self.counters.get(name, 0.0) + value

    def observe(self, name: str, value: float) -> None:
        """observe."""
        self.timers.setdefault(name, []).append(value)

    def set_gauge(self, name: str, value: float) -> None:
        """set_gauge."""
        self.gauges[name] = value

    def record_event(self, name: str) -> None:
        """record_event."""
        self.events.append(name)

    def add_cost(self, name: str, value: float) -> None:
        """add_cost."""
        self.cost[name] = self.cost.get(name, 0.0) + value

    def observe_time(self, name: str, start_time: float) -> None:
        """observe_time."""
        self.observe(name, (time.time() - start_time) * 1000.0)

    def add_carbon(self, energy_kwh: float, co2_kg: float) -> None:
        """add_carbon."""
        self.cost["energy_kwh"] = self.cost.get("energy_kwh", 0.0) + energy_kwh
        self.cost["co2_kg"] = self.cost.get("co2_kg", 0.0) + co2_kg

    def _validate_required(self) -> None:
        """_validate_required."""
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
        """flush."""
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
