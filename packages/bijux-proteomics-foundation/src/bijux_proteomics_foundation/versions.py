# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema-version helpers for additive evolution contracts."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization import JsonModel


class SchemaVersion(JsonModel):
    """Semantic schema version with additive-compatibility helpers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    major: int = Field(..., ge=0)
    minor: int = Field(..., ge=0)
    patch: int = Field(..., ge=0)

    @classmethod
    def parse(cls, value: str) -> SchemaVersion:
        """Parse one dotted semantic version string."""
        parts = value.split(".")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise ValueError(
                f"schema version '{value}' must use 'major.minor.patch' numeric form"
            )
        major, minor, patch = (int(part) for part in parts)
        return cls(major=major, minor=minor, patch=patch)

    def to_string(self) -> str:
        """Return the normalized dotted string representation."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_additive_compatible_with(self, expected: SchemaVersion) -> bool:
        """Return whether this version satisfies additive-evolution expectations."""
        return self.major == expected.major and self.minor >= expected.minor


def normalize_schema_version(value: str) -> str:
    """Normalize one raw schema version string."""
    return SchemaVersion.parse(value).to_string()
