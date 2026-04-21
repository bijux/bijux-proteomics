"""Runtime adapters for runtime memory contracts."""

from __future__ import annotations

from bijux_proteomics_runtime.memory.schemas import MemoryRecord


def memory_record_payload(record: MemoryRecord) -> dict[str, object]:
    """Map memory record to runtime-safe artifact payload."""
    return {
        "record_id": record.record_id,
        "scope": str(record.scope.value),
        "producer": record.producer,
        "created_at": record.created_at.isoformat(),
    }


__all__ = ["MemoryRecord", "memory_record_payload"]
