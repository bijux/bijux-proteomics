# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_foundation.compatibility import (
    SchemaCompatibility,
    SchemaEvolutionAssessment,
    assess_schema_compatibility,
    assess_schema_evolution,
)
from bijux_proteomics_foundation.compatibility.schema_migrations import (
    MigrationRegistry,
    SchemaMigration,
)
from bijux_proteomics_foundation.outcomes.exceptions import (
    MigrationExecutionError,
    MigrationPathError,
)


def test_schema_evolution_assessment_reports_available_migrations() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="raise schema version",
            migrate=lambda payload: {
                **payload,
                "document_schema": {
                    **payload["document_schema"],
                    "schema_version": "1.1.0",
                },
            },
        )
    )

    assessment = assess_schema_evolution(
        observed_version="1.0.0",
        target_version="1.1.0",
        registry=registry,
    )

    assert isinstance(assessment, SchemaEvolutionAssessment)
    assert assessment.migration_required is True
    assert assessment.migration_available is True


def test_schema_evolution_assessment_reports_missing_migration_path() -> None:
    registry = MigrationRegistry()
    assessment = assess_schema_evolution(
        observed_version="1.0.0",
        target_version="1.1.0",
        registry=registry,
    )

    assert assessment.migration_available is False
    assert "no migration path is available" in assessment.notes[1]


def test_assess_schema_compatibility_uses_major_minor_semantics() -> None:
    assert (
        assess_schema_compatibility("1.2.0", "1.1.0") is SchemaCompatibility.COMPATIBLE
    )
    assert (
        assess_schema_compatibility("1.0.0", "1.1.0")
        is SchemaCompatibility.FORWARD_INCOMPATIBLE
    )
    assert (
        assess_schema_compatibility("2.0.0", "1.9.0")
        is SchemaCompatibility.BACKWARD_INCOMPATIBLE
    )


def test_migration_registry_applies_sequential_steps() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="add review cadence",
            migrate=lambda payload: {
                **payload,
                "document_schema": {
                    **payload["document_schema"],
                    "schema_version": "1.1.0",
                },
                "review_cadence": "weekly",
            },
        )
    )
    payload = {
        "document_schema": {"schema_version": "1.0.0"},
        "value": "demo",
    }

    migrated = registry.migrate_to(payload, "1.1.0")

    assert migrated["document_schema"]["schema_version"] == "1.1.0"
    assert migrated["review_cadence"] == "weekly"


def test_migration_registry_reports_registered_versions() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="step one",
            migrate=lambda payload: payload,
        )
    )
    registry.register(
        SchemaMigration(
            from_version="1.1.0",
            to_version="1.2.0",
            description="step two",
            migrate=lambda payload: payload,
        )
    )

    assert registry.registered_versions() == ["1.0.0", "1.1.0", "1.2.0"]


def test_migration_registry_validates_missing_path_with_diagnostics() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="step one",
            migrate=lambda payload: payload,
        )
    )

    with pytest.raises(MigrationPathError, match="known versions: 1.0.0, 1.1.0"):
        registry.validate_path("1.0.0", "1.2.0")


def test_migration_registry_detects_version_mismatch_in_step_output() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="malformed step",
            migrate=lambda payload: {
                **payload,
                "document_schema": {
                    **payload["document_schema"],
                    "schema_version": "1.0.0",
                },
            },
        )
    )
    payload = {"document_schema": {"schema_version": "1.0.0"}}

    with pytest.raises(MigrationExecutionError, match="unexpected schema version"):
        registry.migrate_to(payload, "1.1.0")


def test_migration_registry_blocks_deprecated_target_versions() -> None:
    registry = MigrationRegistry()
    registry.mark_deprecated("1.0.0")

    assert registry.is_deprecated("1.0.0") is True

    with pytest.raises(MigrationPathError, match="is deprecated"):
        registry.migrate_to({"document_schema": {"schema_version": "0.9.0"}}, "1.0.0")
