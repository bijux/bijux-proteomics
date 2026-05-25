# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated drug-target resolution entrypoints."""

from __future__ import annotations

from bijux_proteomics_knowledge.drugs.targets import (
    DrugTargetRelationshipType,
    DrugTargetResolutionEntry,
    DrugTargetResolutionReport,
    DrugTargetResolutionSummary,
    render_drug_target_resolution_tsv,
    resolve_drug_targets,
)

__all__ = [
    "DrugTargetRelationshipType",
    "DrugTargetResolutionEntry",
    "DrugTargetResolutionReport",
    "DrugTargetResolutionSummary",
    "render_drug_target_resolution_tsv",
    "resolve_drug_targets",
]
