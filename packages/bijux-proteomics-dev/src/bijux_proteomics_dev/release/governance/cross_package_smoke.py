# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Ordered cross-package smoke helpers for root API loading and tiny workflows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)

__all__ = [
    "CrossPackageBoundaryCheckpoint",
    "CrossPackageSmokeReport",
    "CrossPackageSmokeStage",
    "PublicPackageApiLoad",
    "ordered_cross_package_boundary_checkpoints",
    "ordered_public_package_modules",
    "render_cross_package_smoke_summary",
    "load_public_package_apis",
    "run_cross_package_smoke_workflow",
    "run_foundation_core_knowledge_smoke",
    "run",
    "validate_cross_package_smoke_report",
]


@dataclass(frozen=True)
class PublicPackageApiLoad:
    """One ordered public package root with its loaded exports."""

    package_name: str
    module_name: str
    export_names: tuple[str, ...]


@dataclass(frozen=True)
class CrossPackageSmokeStage:
    """One ordered package boundary crossed by the smoke workflow."""

    package_name: str
    stage_name: str
    summary: str


@dataclass(frozen=True)
class CrossPackageSmokeReport:
    """Cross-package smoke report with explicit ordered stage outputs."""

    public_root_loads: tuple[PublicPackageApiLoad, ...]
    stages: tuple[CrossPackageSmokeStage, ...]
    canonical_payload_hash: str
    canonical_payload_json: str
    canonical_accession: str
    sequence_length: int
    knowledge_pathway_id: str
    knowledge_coverage_fraction: float
    recommendation_id: str | None = None
    recommendation_type: str | None = None
    runtime_run_id: str | None = None
    runtime_downstream_surface: str | None = None
    runtime_app_title: str | None = None
    runtime_summary_path: str | None = None


@dataclass(frozen=True)
class CrossPackageBoundaryCheckpoint:
    """One explicit ordered package boundary that the smoke workflow must cross."""

    package_name: str
    stage_name: str
    boundary_symbol: str


def ordered_public_package_modules() -> tuple[tuple[str, str], ...]:
    """Return the canonical product-package root order for smoke loading."""

    return (
        ("foundation", "bijux_proteomics_foundation"),
        ("core", "bijux_proteomics"),
        ("knowledge", "bijux_proteomics_knowledge"),
        ("intelligence", "bijux_proteomics_intelligence"),
        ("runtime", "bijux_proteomics_runtime"),
    )


def load_public_package_apis() -> tuple[PublicPackageApiLoad, ...]:
    """Import every product-package root and force all curated root exports to load."""

    loaded: list[PublicPackageApiLoad] = []
    for package_name, module_name in ordered_public_package_modules():
        module = import_module(module_name)
        export_names = tuple(getattr(module, "__all__", ()))
        for export_name in export_names:
            _ = getattr(module, export_name)
        loaded.append(
            PublicPackageApiLoad(
                package_name=package_name,
                module_name=module_name,
                export_names=export_names,
            )
        )
    return tuple(loaded)


def ordered_cross_package_boundary_checkpoints() -> tuple[CrossPackageBoundaryCheckpoint, ...]:
    """Return the canonical ordered boundary chain for the smoke workflow."""

    return (
        CrossPackageBoundaryCheckpoint(
            package_name="foundation",
            stage_name="canonical_payload",
            boundary_symbol="bijux_proteomics_foundation.hash_payload",
        ),
        CrossPackageBoundaryCheckpoint(
            package_name="core",
            stage_name="parse_fasta_document",
            boundary_symbol="bijux_proteomics.parse_fasta_document",
        ),
        CrossPackageBoundaryCheckpoint(
            package_name="knowledge",
            stage_name="resolve_pathway_members",
            boundary_symbol="bijux_proteomics_knowledge.resolve_pathway_members",
        ),
        CrossPackageBoundaryCheckpoint(
            package_name="intelligence",
            stage_name="recommend_next_experiments",
            boundary_symbol=(
                "bijux_proteomics_intelligence.next_steps.recommend_next_experiments"
            ),
        ),
        CrossPackageBoundaryCheckpoint(
            package_name="runtime",
            stage_name="run_reviewable_sequence_path",
            boundary_symbol=(
                "bijux_proteomics_runtime.workflows.run_reviewable_sequence_path"
            ),
        ),
    )


def run_foundation_core_knowledge_smoke(
    repo_root: Path | None = None,
) -> CrossPackageSmokeReport:
    """Run the tiny smoke chain through foundation, core, and knowledge."""

    public_root_loads = load_public_package_apis()

    from bijux_proteomics import parse_fasta_document
    from bijux_proteomics_foundation import (
        DocumentSchema,
        hash_payload,
        to_canonical_json,
    )
    from bijux_proteomics_knowledge import (
        KnowledgeCoverageEntitySet,
        KnowledgeCoverageEntityType,
        compute_knowledge_coverage,
        evaluate_schema_compatibility,
        resolve_pathway_members,
    )

    schema = DocumentSchema(
        schema_version="1.0.0",
        created_by="cross-package-smoke",
    )
    fasta_payload = _smoke_fasta_payload()
    payload = {
        "schema_version": schema.schema_version,
        "fasta_payload": fasta_payload,
        "repo_root": "" if repo_root is None else str(repo_root),
    }
    canonical_payload_json = to_canonical_json(payload)
    canonical_payload_hash = hash_payload(payload)

    fasta_report = parse_fasta_document(fasta_payload)
    accepted_record = fasta_report.accepted_records[0]

    _ = evaluate_schema_compatibility(schema)
    annotation_pack = _smoke_annotation_pack()
    coverage_report = compute_knowledge_coverage(
        (
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.PROTEIN,
                entity_ids=(accepted_record.canonical_accession,),
            ),
        ),
        annotation_pack,
    )
    pathway_report = resolve_pathway_members(
        (accepted_record.canonical_accession,),
        annotation_pack,
    )

    return CrossPackageSmokeReport(
        public_root_loads=public_root_loads,
        stages=(
            CrossPackageSmokeStage(
                package_name="foundation",
                stage_name="canonical_payload",
                summary="foundation produced the canonical smoke payload and schema envelope",
            ),
            CrossPackageSmokeStage(
                package_name="core",
                stage_name="parse_fasta_document",
                summary="core parsed one canonical FASTA record into a normalized accession",
            ),
            CrossPackageSmokeStage(
                package_name="knowledge",
                stage_name="resolve_pathway_members",
                summary="knowledge grounded the parsed accession onto one pathway with explicit missing members",
            ),
        ),
        canonical_payload_hash=canonical_payload_hash,
        canonical_payload_json=canonical_payload_json,
        canonical_accession=accepted_record.canonical_accession,
        sequence_length=len(accepted_record.residues),
        knowledge_pathway_id=pathway_report.entries[0].pathway_id,
        knowledge_coverage_fraction=coverage_report.entries[0].coverage_fraction,
    )


def run_cross_package_smoke_workflow(base_dir: Path) -> CrossPackageSmokeReport:
    """Run the full tiny smoke workflow through all product packages."""

    foundation_core_knowledge = run_foundation_core_knowledge_smoke(base_dir)

    from bijux_proteomics.workflow.interactive_result_bundle import (
        InteractiveResultBundle,
        InteractiveResultBundleSummary,
        InteractiveResultPathway,
    )
    from bijux_proteomics.workflow.study_result import (
        ProteomicsStudyDesignEntry,
        ProteomicsStudyDesignSnapshot,
        ProteomicsStudyKind,
        ProteomicsStudyResult,
        ProteomicsStudyResultSummary,
    )
    from bijux_proteomics_intelligence import next_steps
    from bijux_proteomics_runtime import AppConfig, create_app
    from bijux_proteomics_runtime.workflows import run_reviewable_sequence_path

    recommendation_report = next_steps.recommend_next_experiments(
        ProteomicsStudyResult(
            study_kind=ProteomicsStudyKind.ARCHIVED,
            source_surface="cross-package-smoke",
            design=ProteomicsStudyDesignSnapshot(
                entries=(
                    ProteomicsStudyDesignEntry(
                        sample_id="S1",
                        condition="treated",
                    ),
                ),
                sample_count=1,
                condition_count=1,
                batch_count=0,
                paired_sample_count=0,
                multiplexed_sample_count=0,
                note="cross-package smoke design",
            ),
            interactive_result_bundle=InteractiveResultBundle(
                source_reports=(),
                summary=InteractiveResultBundleSummary(
                    biological_report_available=True,
                    ptm_report_available=False,
                    run_qc_input_count=0,
                    sample_count=1,
                    protein_count=0,
                    peptide_count=0,
                    ptm_site_count=0,
                    pathway_count=1,
                    qc_entry_count=0,
                    card_count=0,
                    graph_node_count=0,
                    graph_edge_count=0,
                    plot_count=0,
                ),
                samples=(),
                proteins=(),
                peptides=(),
                ptm_sites=(),
                pathways=(
                    InteractiveResultPathway(
                        pathway_id=foundation_core_knowledge.knowledge_pathway_id,
                        adjusted_p_value=0.04,
                        supporting_protein_refs=(
                            foundation_core_knowledge.canonical_accession,
                        ),
                        unresolved_member_ids=("SIGB",),
                    ),
                ),
                qc_entries=(),
                cards=(),
                graph_nodes=(),
                graph_edges=(),
                plots=(),
                note="cross-package smoke pathway bundle",
            ),
            summary=ProteomicsStudyResultSummary(
                design_entry_count=1,
                matrix_surface_count=0,
                statistic_surface_count=0,
                qc_surface_count=0,
                card_surface_count=0,
                conclusion_count=0,
            ),
            note="cross-package smoke study result",
        )
    )
    recommendation = recommendation_report.entries[0]

    app = create_app(
        AppConfig(
            base_dir=base_dir,
            docs_enabled=False,
            title=f"cross-package-{recommendation.recommendation_type.value}",
        )
    )
    runtime_manifest = run_reviewable_sequence_path(
        base_dir,
        sequence=_smoke_sequence(),
        execution_mode="cpu",
    )

    return CrossPackageSmokeReport(
        public_root_loads=foundation_core_knowledge.public_root_loads,
        stages=(
            *foundation_core_knowledge.stages,
            CrossPackageSmokeStage(
                package_name="intelligence",
                stage_name="recommend_next_experiments",
                summary="intelligence converted the knowledge gap into one explicit follow-up experiment recommendation",
            ),
            CrossPackageSmokeStage(
                package_name="runtime",
                stage_name="run_reviewable_sequence_path",
                summary="runtime published a reviewable execution output for the same tiny sequence",
            ),
        ),
        canonical_payload_hash=foundation_core_knowledge.canonical_payload_hash,
        canonical_payload_json=foundation_core_knowledge.canonical_payload_json,
        canonical_accession=foundation_core_knowledge.canonical_accession,
        sequence_length=foundation_core_knowledge.sequence_length,
        knowledge_pathway_id=foundation_core_knowledge.knowledge_pathway_id,
        knowledge_coverage_fraction=foundation_core_knowledge.knowledge_coverage_fraction,
        recommendation_id=recommendation.recommendation_id,
        recommendation_type=recommendation.recommendation_type.value,
        runtime_run_id=runtime_manifest.run_id,
        runtime_downstream_surface=runtime_manifest.downstream_surface,
        runtime_app_title=app.title,
        runtime_summary_path=runtime_manifest.summary_path,
    )


def _smoke_annotation_pack() -> AnnotationPack:
    return AnnotationPack(
        source_path="cross-package-smoke-annotation-pack.json",
        pack_name="cross-package-smoke-annotation-pack",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="P04637",
                gene_symbol="TP53",
                description="tumor protein p53",
            ),
        ),
        pathways=(
            PathwayMembershipRecord(
                pathway_id="pathway:guardian_response",
                member_kind=PathwayMemberKind.PROTEIN,
                member_id="P04637",
            ),
            PathwayMembershipRecord(
                pathway_id="pathway:guardian_response",
                member_kind=PathwayMemberKind.GENE,
                member_id="SIGB",
            ),
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=1,
            pathway_count=2,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=0,
            ortholog_count=0,
        ),
    )


def _smoke_fasta_payload() -> str:
    return (
        ">sp|P04637|TP53_HUMAN tumor protein p53\n"
        "MEEPQSDPSVEPPLSQETFSDLWKLLPEN\n"
    )


def _smoke_sequence() -> str:
    return "MEEPQSDPSVEPPLSQETFSDLWKLLPEN"


def validate_cross_package_smoke_report(
    report: CrossPackageSmokeReport,
) -> tuple[str, ...]:
    """Return ordered smoke-boundary issues for the first broken checkpoint onward."""

    actual = tuple((stage.package_name, stage.stage_name) for stage in report.stages)
    expected = tuple(
        (checkpoint.package_name, checkpoint.stage_name)
        for checkpoint in ordered_cross_package_boundary_checkpoints()
    )
    issues: list[str] = []
    for index, checkpoint in enumerate(ordered_cross_package_boundary_checkpoints()):
        if index >= len(actual):
            issues.append(
                f"missing boundary {checkpoint.package_name}.{checkpoint.stage_name} "
                f"at {checkpoint.boundary_symbol}"
            )
            break
        actual_package_name, actual_stage_name = actual[index]
        if (actual_package_name, actual_stage_name) != (
            checkpoint.package_name,
            checkpoint.stage_name,
        ):
            issues.append(
                "first broken boundary is "
                f"{checkpoint.package_name}.{checkpoint.stage_name} at "
                f"{checkpoint.boundary_symbol}; got "
                f"{actual_package_name}.{actual_stage_name}"
            )
            break
    if not issues and actual != expected:
        issues.append("unexpected extra smoke stages appear after the canonical boundary chain")
    return tuple(issues)


def render_cross_package_smoke_summary(report: CrossPackageSmokeReport) -> str:
    """Render a stable human-readable smoke summary with boundary checkpoints."""

    lines = [
        "cross-package smoke workflow",
        f"- root package loads: {', '.join(load.package_name for load in report.public_root_loads)}",
        f"- canonical accession: {report.canonical_accession}",
        f"- knowledge pathway: {report.knowledge_pathway_id}",
    ]
    if report.recommendation_id is not None:
        lines.append(f"- intelligence recommendation: {report.recommendation_id}")
    if report.runtime_run_id is not None:
        lines.append(f"- runtime run id: {report.runtime_run_id}")
    lines.append("- boundaries:")
    for checkpoint in ordered_cross_package_boundary_checkpoints():
        lines.append(
            f"  - {checkpoint.package_name}.{checkpoint.stage_name}: {checkpoint.boundary_symbol}"
        )
    return "\n".join(lines)


def run(repo_root: Path | None = None) -> int:
    """Execute the cross-package smoke workflow and print a stable summary."""

    report = run_cross_package_smoke_workflow(repo_root or Path.cwd() / "artifacts" / "cross-package-smoke")
    issues = validate_cross_package_smoke_report(report)
    print(render_cross_package_smoke_summary(report))
    if issues:
        for issue in issues:
            print(issue)
        return 1
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the ordered cross-package public API smoke workflow.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional directory for smoke runtime outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = None if args.repo_root is None else Path(args.repo_root)
    return run(repo_root=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
