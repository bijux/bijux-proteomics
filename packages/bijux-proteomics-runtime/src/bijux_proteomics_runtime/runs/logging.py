# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Structured runtime logging helpers."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


class StructuredLogger:
    """Append-only structured logger for one runtime run."""

    def __init__(
        self, run_id: str, log_path: Path, base_component: str | None = None
    ) -> None:
        self._run_id = run_id
        self._log_path = log_path
        self._base_component = base_component

    def log(
        self,
        component: str | None,
        event: str,
        status: str,
        duration_ms: float,
        **fields: Any,
    ) -> None:
        """Persist one structured runtime log event."""
        component_value = component or self._base_component or "runtime"
        if (
            self._base_component
            and component
            and not component.startswith(self._base_component)
        ):
            component_value = f"{self._base_component}.{component}"
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": self._run_id,
            "component": component_value,
            "event": event,
            "duration_ms": round(float(duration_ms), 3),
            "status": status,
        }
        payload.update(fields)
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True) + "\n")

    def scope(self, component: str) -> StructuredLogger:
        """Return a logger with a nested runtime component prefix."""
        return StructuredLogger(
            run_id=self._run_id,
            log_path=self._log_path,
            base_component=component,
        )


class NoopStructuredLogger(StructuredLogger):
    """Structured logger that deliberately emits nothing."""

    def __init__(self) -> None:
        super().__init__(run_id="noop", log_path=Path("noop"))

    def log(
        self,
        component: str | None,
        event: str,
        status: str,
        duration_ms: float,
        **fields: Any,
    ) -> None:
        return

    def scope(self, component: str) -> StructuredLogger:
        return self


__all__ = ["NoopStructuredLogger", "StructuredLogger"]
