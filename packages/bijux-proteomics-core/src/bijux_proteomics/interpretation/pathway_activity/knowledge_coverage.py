# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Knowledge coverage lookup for pathway activity scoring."""

from __future__ import annotations

from bijux_proteomics.interpretation.pathway_activity.models import PathwayActivityPolicy
from bijux_proteomics.interpretation.pathway_enrichment import PathwayMembershipRecord

from bijux_proteomics_knowledge.pathways.members import (
    PathwayCoveragePolicy,
    resolve_pathway_members,
)


def pathway_coverage_by_id(
    available_protein_refs: set[str],
    pathway_records: tuple[PathwayMembershipRecord, ...],
    *,
    policy: PathwayActivityPolicy,
) -> dict[str, object]:
    """Resolve pathway knowledge coverage entries keyed by pathway identifier."""

    coverage_report = resolve_pathway_members(
        tuple(sorted(available_protein_refs)),
        pathway_records,
        policy=PathwayCoveragePolicy(
            minimum_coverage_fraction=policy.minimum_knowledge_coverage_fraction
        ),
    )
    return {
        entry.pathway_id: entry for entry in coverage_report.confidence_entries
    }
