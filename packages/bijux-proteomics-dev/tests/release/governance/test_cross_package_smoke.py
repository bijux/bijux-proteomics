# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    run_foundation_core_knowledge_smoke,
)


def test_cross_package_smoke_foundation_core_knowledge_chain_stays_coherent() -> None:
    report = run_foundation_core_knowledge_smoke()

    assert tuple(stage.package_name for stage in report.stages) == (
        "foundation",
        "core",
        "knowledge",
    )
    assert tuple(stage.stage_name for stage in report.stages) == (
        "canonical_payload",
        "parse_fasta_document",
        "resolve_pathway_members",
    )
    assert report.canonical_accession == "P04637"
    assert report.sequence_length == 29
    assert report.knowledge_pathway_id == "pathway:guardian_response"
    assert report.knowledge_coverage_fraction == 1.0
    assert '"schema_version":"1.0.0"' in report.canonical_payload_json
    assert len(report.canonical_payload_hash) == 64


def test_cross_package_smoke_foundation_core_knowledge_chain_keeps_root_imports_attached() -> (
    None
):
    report = run_foundation_core_knowledge_smoke(Path("/tmp/cross-package-smoke"))

    assert tuple(load.package_name for load in report.public_root_loads) == (
        "foundation",
        "core",
        "knowledge",
        "intelligence",
        "runtime",
    )
    assert all(load.export_names for load in report.public_root_loads)
