# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Schema migration primitives for durable document evolution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization import JsonModel

MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


class SchemaMigration(JsonModel):
    """One migration step between schema versions."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    from_version: str = Field(..., min_length=1, description="Source schema version.")
    to_version: str = Field(..., min_length=1, description="Target schema version.")
    description: str = Field(..., min_length=1, description="Why the migration exists.")
    migrate: MigrationFn = Field(..., description="Migration function.")


class MigrationRegistry:
    """Registry for schema migration steps."""

    def __init__(self) -> None:
        self._migrations: dict[str, SchemaMigration] = {}

    def register(self, migration: SchemaMigration) -> None:
        """Register one migration by its source version."""
        self._migrations[migration.from_version] = migration

    def migrate_to(self, payload: dict[str, Any], target_version: str) -> dict[str, Any]:
        """Apply sequential migrations until target version is reached."""
        current = payload.get("document_schema", {}).get("schema_version")
        if current is None:
            return payload
        result = dict(payload)
        while current != target_version:
            step = self._migrations.get(current)
            if step is None:
                raise ValueError(f"missing migration step from {current} to {target_version}")
            result = step.migrate(result)
            current = result["document_schema"]["schema_version"]
        return result
