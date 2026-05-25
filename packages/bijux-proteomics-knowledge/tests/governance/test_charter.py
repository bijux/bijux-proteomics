# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.governance.charter import (
    DEFAULT_KNOWLEDGE_CHARTER,
    DEFAULT_KNOWLEDGE_MODULE_AUDIT,
    KnowledgeCharterCapability,
    KnowledgeModuleClassification,
)

KNOWLEDGE_SRC_ROOT = Path(
    "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"
)


def test_knowledge_charter_defines_exact_grounding_capabilities() -> None:
    capabilities = {entry.capability for entry in DEFAULT_KNOWLEDGE_CHARTER}

    assert capabilities == {
        KnowledgeCharterCapability.REFERENCES,
        KnowledgeCharterCapability.ONTOLOGIES,
        KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
        KnowledgeCharterCapability.CURATED_CORPORA,
        KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
    }


def test_knowledge_module_audit_covers_every_source_module() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_KNOWLEDGE_MODULE_AUDIT}
    source_paths = {
        path.relative_to(KNOWLEDGE_SRC_ROOT).as_posix()
        for path in KNOWLEDGE_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths


def test_knowledge_module_audit_rejects_duplicate_and_wrong_owner_entries() -> None:
    duplicate_or_wrong = {
        entry.module_path: entry.classification
        for entry in DEFAULT_KNOWLEDGE_MODULE_AUDIT
        if entry.classification
        in {
            KnowledgeModuleClassification.DUPLICATE_MODEL,
            KnowledgeModuleClassification.WRONG_PACKAGE_LOGIC,
        }
    }

    assert duplicate_or_wrong == {}


def test_knowledge_thin_modules_are_only_roots_and_compatibility_wrappers() -> None:
    thin_placeholders = {
        entry.module_path
        for entry in DEFAULT_KNOWLEDGE_MODULE_AUDIT
        if entry.classification is KnowledgeModuleClassification.THIN_PLACEHOLDER
    }

    assert thin_placeholders == {
        "__init__.py",
        "complexes/__init__.py",
        "contracts/__init__.py",
        "features/__init__.py",
        "governance/__init__.py",
        "identity/__init__.py",
        "memory/__init__.py",
        "memory/integrity/__init__.py",
        "memory/models/__init__.py",
        "memory/normalization/__init__.py",
        "memory/reconciliation/__init__.py",
        "pathways/__init__.py",
        "references/__init__.py",
        "references/grounding/__init__.py",
        "references/public.py",
        "references/workflows/__init__.py",
        "reviews/__init__.py",
    }
