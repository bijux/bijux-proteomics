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

    def registered_versions(self) -> list[str]:
        """Return all versions that participate in known migration edges."""
        versions = {
            version
            for migration in self._migrations.values()
            for version in (migration.from_version, migration.to_version)
        }
        return sorted(versions)

    def migration_path(self, from_version: str, target_version: str) -> list[SchemaMigration]:
        """Return the ordered migration path needed to reach the target version."""
        if from_version == target_version:
            return []
        path: list[SchemaMigration] = []
        current = from_version
        seen: set[str] = set()
        while current != target_version:
            if current in seen:
                raise ValueError(
                    f"detected migration cycle while resolving path from {from_version} to {target_version}"
                )
            seen.add(current)
            step = self._migrations.get(current)
            if step is None:
                known = ", ".join(self.registered_versions()) or "none"
                raise ValueError(
                    f"missing migration step from {current} toward {target_version}; known versions: {known}"
                )
            path.append(step)
            current = step.to_version
        return path

    def validate_path(self, from_version: str, target_version: str) -> None:
        """Validate that the migration path exists and has no loops."""
        self.migration_path(from_version, target_version)

    def migrate_to(self, payload: dict[str, Any], target_version: str) -> dict[str, Any]:
        """Apply sequential migrations until target version is reached."""
        current = payload.get("document_schema", {}).get("schema_version")
        if current is None:
            return payload
        result = dict(payload)
        for step in self.migration_path(current, target_version):
            result = step.migrate(result)
            current = result.get("document_schema", {}).get("schema_version")
            if current != step.to_version:
                raise ValueError(
                    "migration step produced an unexpected schema version: "
                    f"expected {step.to_version}, got {current}"
                )
        return result
