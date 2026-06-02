# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Protocol

import pytest

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
SUPPORT_PATH = Path(__file__).with_name("public_api_smoke_support.py")


class _PublicApiSmokeSupport(Protocol):
    def load_public_package_apis(self) -> tuple["_PublicPackageApiLoad", ...]: ...

    def ordered_public_package_modules(self) -> tuple[tuple[str, str], ...]: ...


class _PublicPackageApiLoad(Protocol):
    package_name: str
    module_name: str
    export_names: tuple[str, ...]


def _load_support_module() -> _PublicApiSmokeSupport:
    spec = importlib.util.spec_from_file_location(
        "bijux_proteomics_dev_public_api_smoke_support",
        SUPPORT_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    assert isinstance(module, ModuleType)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SUPPORT = _load_support_module()
load_public_package_apis = _SUPPORT.load_public_package_apis
ordered_public_package_modules = _SUPPORT.ordered_public_package_modules


def _product_source_pythonpath() -> str:
    roots = (
        "packages/agentic-proteins/src",
        "packages/bijux-proteomics/src",
        "packages/bijux-proteomics-core/src",
        "packages/bijux-proteomics-foundation/src",
        "packages/bijux-proteomics-intelligence/src",
        "packages/bijux-proteomics-knowledge/src",
        "packages/bijux-proteomics-lab/src",
        "packages/bijux-proteomics-runtime/src",
        "packages/proteomics/src",
        "packages/proteomics-core/src",
        "packages/proteomics-foundation/src",
        "packages/proteomics-intelligence/src",
        "packages/proteomics-knowledge/src",
        "packages/proteomics-lab/src",
        "packages/proteomics-runtime/src",
        "packages/bijux-proteomics-dev/tests/package",
    )
    return ":".join(str(REPO_ROOT / root) for root in roots)


def test_cross_package_public_api_smoke_loads_every_root_export_in_order() -> None:
    loads = load_public_package_apis()

    assert tuple((load.package_name, load.module_name) for load in loads) == (
        ordered_public_package_modules()
    )
    assert tuple(load.export_names for load in loads) == (
        (
            "AssayId",
            "BatchId",
            "CandidateId",
            "ClaimId",
            "DocumentSchema",
            "EvidenceId",
            "fingerprint_model",
            "GateId",
            "hash_model",
            "hash_payload",
            "hash_text",
            "JsonModel",
            "ProgramId",
            "TargetId",
            "to_canonical_json",
        ),
        (
            "DigestPolicy",
            "parse_fasta_document",
            "parse_experimental_design_table",
            "build_normalized_run_bundle",
            "build_fdr_audit_trail",
        ),
        (
            "EvidenceBundle",
            "EvidenceClaim",
            "EvidenceRecord",
            "ComplexCoveragePolicy",
            "ComplexMembershipConfidence",
            "ComplexMembershipResolutionEntry",
            "ComplexMembershipResolutionReport",
            "ComplexMembershipResolutionSummary",
            "DiseaseTermResolutionEntry",
            "DiseaseTermResolutionReport",
            "DiseaseTermResolutionSummary",
            "KnowledgeCoverageEntitySet",
            "KnowledgeCoverageEntityType",
            "KnowledgeCoverageEntry",
            "KnowledgeCoveragePolicy",
            "KnowledgeCoverageReport",
            "KnowledgeCoverageSummary",
            "CrossSpeciesOrthologAmbiguity",
            "CrossSpeciesOrthologEntry",
            "CrossSpeciesOrthologEvidenceStatus",
            "CrossSpeciesOrthologReport",
            "CrossSpeciesOrthologSummary",
            "DrugTargetRelationshipType",
            "DrugTargetResolutionEntry",
            "DrugTargetResolutionReport",
            "DrugTargetResolutionSummary",
            "KnowledgeDecisionBrief",
            "KinaseSubstrateMatchType",
            "KinaseSubstrateResolutionEntry",
            "KinaseSubstrateResolutionReport",
            "KinaseSubstrateResolutionSummary",
            "PathwayCoverageConfidenceEntry",
            "PathwayCoverageConfidenceStatus",
            "PathwayCoveragePolicy",
            "PathwayMembershipResolutionEntry",
            "PathwayMembershipResolutionReport",
            "PathwayMembershipResolutionSummary",
            "ProteinFeatureOverlapEntry",
            "ProteinFeatureQueryInterval",
            "ProteinFeatureType",
            "ProteinIdResolutionEntry",
            "ProteinIdentityResolutionStatus",
            "evaluate_schema_compatibility",
            "overlap_protein_features",
            "render_complex_membership_resolution_tsv",
            "render_disease_term_resolution_tsv",
            "render_drug_target_resolution_tsv",
            "render_kinase_substrate_resolution_tsv",
            "render_knowledge_coverage_tsv",
            "render_cross_species_ortholog_tsv",
            "render_pathway_membership_resolution_tsv",
            "render_protein_feature_overlaps_tsv",
            "render_protein_id_resolution_tsv",
            "compute_knowledge_coverage",
            "map_cross_species_orthologs",
            "resolve_complex_members",
            "resolve_disease_terms",
            "resolve_drug_targets",
            "resolve_kinase_substrates",
            "resolve_pathway_members",
            "resolve_protein_ids",
        ),
        (
            "belief_audit",
            "candidates",
            "claims",
            "contradictions",
            "falsifiers",
            "governance",
            "interpretation",
            "judgment",
            "learning",
            "next_steps",
            "posture",
            "query",
            "refusal",
            "reviews",
        ),
        ("AppConfig", "RunManager", "cli", "create_app"),
    )


@pytest.mark.slow
def test_cross_package_public_api_smoke_does_not_require_dev_package_imports() -> None:
    code = """
import builtins

from public_api_smoke_support import load_public_package_apis

original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "bijux_proteomics_dev" or name.startswith("bijux_proteomics_dev."):
        raise ModuleNotFoundError(f"blocked import: {name}")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
loads = load_public_package_apis()
assert tuple(load.package_name for load in loads) == (
    "foundation",
    "core",
    "knowledge",
    "intelligence",
    "runtime",
)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": _product_source_pythonpath()},
        check=False,
    )
    assert result.returncode == 0, result.stderr
