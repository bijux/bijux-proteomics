# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Ordered cross-package smoke helpers for root API loading and tiny workflows."""

from __future__ import annotations

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
    "CrossPackageSmokeReport",
    "CrossPackageSmokeStage",
    "PublicPackageApiLoad",
    "ordered_public_package_modules",
    "load_public_package_apis",
    "run_foundation_core_knowledge_smoke",
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
