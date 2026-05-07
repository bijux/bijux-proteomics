# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
)
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    ScientificGraduationState,
    build_repository_science_table_report,
    build_scientific_release_packet,
)


def test_repository_science_table_report_covers_all_packages() -> None:
    report = build_repository_science_table_report()

    assert {table.package_name for table in report.tables} == {
        "agentic-proteins",
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
        "bijux-proteomics-dev",
    }


def test_scientific_release_packet_blocks_graduation_for_curated_fixture_tier() -> None:
    manifest = get_benchmark_manifest("benchmark:targeted_transition_quality_control")
    assert manifest is not None

    packet = build_scientific_release_packet(manifest)

    assert packet.workflow_family.value == "targeted"
    assert packet.threshold_evidence.entries
    assert packet.failure_trap_report.entries
    assert packet.hostile_reviewer_checklist.items
    assert packet.flagship_reproducibility_pack.artifact_ids
    assert packet.graduation_state is ScientificGraduationState.BLOCKED
    assert packet.evidence_quality_gate_passed is False
