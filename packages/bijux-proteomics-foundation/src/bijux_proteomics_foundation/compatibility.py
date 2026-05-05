# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema compatibility assessments for durable document metadata."""

from __future__ import annotations

from enum import StrEnum

from bijux_proteomics_foundation.versions import SchemaVersion


class SchemaCompatibility(StrEnum):
    """Compatibility status for expected versus observed schema versions."""

    COMPATIBLE = "compatible"
    FORWARD_INCOMPATIBLE = "forward_incompatible"
    BACKWARD_INCOMPATIBLE = "backward_incompatible"


def assess_schema_compatibility(
    observed: str,
    expected: str,
) -> SchemaCompatibility:
    """Assess compatibility using major and minor version semantics."""
    observed_version = SchemaVersion.parse(observed)
    expected_version = SchemaVersion.parse(expected)
    if observed_version.major != expected_version.major:
        return SchemaCompatibility.BACKWARD_INCOMPATIBLE
    if not observed_version.is_additive_compatible_with(expected_version):
        return SchemaCompatibility.FORWARD_INCOMPATIBLE
    return SchemaCompatibility.COMPATIBLE


__all__ = ["SchemaCompatibility", "assess_schema_compatibility"]
