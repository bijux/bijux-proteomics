# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable knowledge document and schema contracts."""

from __future__ import annotations

from bijux_proteomics_knowledge.contracts.schema import (
    KnowledgeSchemaProfile,
    SchemaCompatibilityReport,
    default_knowledge_schema_profile,
    evaluate_schema_compatibility,
)

__all__ = [
    "KnowledgeSchemaProfile",
    "SchemaCompatibilityReport",
    "default_knowledge_schema_profile",
    "evaluate_schema_compatibility",
]
