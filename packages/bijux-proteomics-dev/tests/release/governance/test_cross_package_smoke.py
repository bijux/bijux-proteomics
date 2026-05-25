# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from bijux_proteomics_dev.release.governance.cross_package_smoke import (
    CrossPackageSmokeStage,
    render_cross_package_smoke_summary,
    run_cross_package_smoke_workflow,
    run_foundation_core_knowledge_smoke,
    validate_cross_package_smoke_report,
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


def test_cross_package_smoke_workflow_crosses_intelligence_and_runtime(tmp_path: Path) -> (
    None
):
    report = run_cross_package_smoke_workflow(tmp_path)

    assert tuple(stage.package_name for stage in report.stages) == (
        "foundation",
        "core",
        "knowledge",
        "intelligence",
        "runtime",
    )
    assert tuple(stage.stage_name for stage in report.stages) == (
        "canonical_payload",
        "parse_fasta_document",
        "resolve_pathway_members",
        "recommend_next_experiments",
        "run_reviewable_sequence_path",
    )
    assert report.recommendation_id == (
        "pathway_member_resolution:pathway:guardian_response"
    )
    assert report.recommendation_type == "pathway_member_resolution"
    assert report.runtime_downstream_surface == "intelligence_review"
    assert report.runtime_app_title == "cross-package-pathway_member_resolution"
    assert report.runtime_run_id is not None
    assert report.runtime_summary_path is not None
    assert Path(report.runtime_summary_path).exists()


def test_cross_package_smoke_summary_lists_ordered_boundary_symbols(
    tmp_path: Path,
) -> None:
    report = run_cross_package_smoke_workflow(tmp_path)

    assert render_cross_package_smoke_summary(report).splitlines() == [
        "cross-package smoke workflow",
        "- root package loads: foundation, core, knowledge, intelligence, runtime",
        "- canonical accession: P04637",
        "- knowledge pathway: pathway:guardian_response",
        "- intelligence recommendation: pathway_member_resolution:pathway:guardian_response",
        f"- runtime run id: {report.runtime_run_id}",
        "- boundaries:",
        "  - foundation.canonical_payload: bijux_proteomics_foundation.hash_payload",
        "  - core.parse_fasta_document: bijux_proteomics.parse_fasta_document",
        "  - knowledge.resolve_pathway_members: bijux_proteomics_knowledge.resolve_pathway_members",
        "  - intelligence.recommend_next_experiments: bijux_proteomics_intelligence.next_steps.recommend_next_experiments",
        "  - runtime.run_reviewable_sequence_path: bijux_proteomics_runtime.workflows.run_reviewable_sequence_path",
    ]


def test_cross_package_smoke_validation_names_the_first_broken_boundary(
    tmp_path: Path,
) -> None:
    report = run_cross_package_smoke_workflow(tmp_path)
    broken = replace(
        report,
        stages=(
            report.stages[0],
            report.stages[1],
            CrossPackageSmokeStage(
                package_name="runtime",
                stage_name="run_reviewable_sequence_path",
                summary="broken ordering",
            ),
            *report.stages[3:],
        ),
    )

    assert validate_cross_package_smoke_report(broken) == (
        "first broken boundary is knowledge.resolve_pathway_members at "
        "bijux_proteomics_knowledge.resolve_pathway_members; got "
        "runtime.run_reviewable_sequence_path",
    )
