# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import bijux_proteomics_knowledge as knowledge
from bijux_proteomics_knowledge.charter import (
    DEFAULT_KNOWLEDGE_MODULE_AUDIT,
    KnowledgeModuleClassification,
)
from bijux_proteomics_knowledge.references import (
    DEFAULT_BENCHMARK_MANIFESTS,
    DEFAULT_CITATION_REGISTRY,
    DEFAULT_CORPUS_MANIFESTS,
    DEFAULT_KNOWN_PROBLEM_REGISTRY,
    DEFAULT_LITERATURE_GROUPS,
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    DEFAULT_WORKFLOW_NARRATIVES,
    KnowledgeWorkflowFamily,
    build_workflow_reference_briefing,
)


KNOWLEDGE_SRC_ROOT = Path(
    "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "bijux_proteomics_runtime",
    "bijux_proteomics_intelligence",
)
VAGUE_GROUNDING_PHRASES = (
    "internal note",
    "internal notes",
    "todo",
    "tbd",
    "placeholder",
)


def _import_targets(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
            continue
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            targets.add(node.module)
    return targets


def test_knowledge_source_does_not_import_runtime_or_intelligence() -> None:
    violating_modules: dict[str, set[str]] = {}

    for path in KNOWLEDGE_SRC_ROOT.rglob("*.py"):
        imported_modules = _import_targets(path)
        forbidden = {
            module
            for module in imported_modules
            if module.startswith(FORBIDDEN_IMPORT_PREFIXES)
        }
        if forbidden:
            violating_modules[path.relative_to(KNOWLEDGE_SRC_ROOT).as_posix()] = (
                forbidden
            )

    assert violating_modules == {}


def test_knowledge_package_keeps_substantial_scientific_memory_surface() -> None:
    curated_modules = [
        entry
        for entry in DEFAULT_KNOWLEDGE_MODULE_AUDIT
        if entry.classification is KnowledgeModuleClassification.CURATED_REFERENCE_VALUE
    ]

    assert len(curated_modules) >= 18
    assert len(DEFAULT_CITATION_REGISTRY) >= 8
    assert len(DEFAULT_BENCHMARK_MANIFESTS) >= 6
    assert len(DEFAULT_CORPUS_MANIFESTS) >= 10
    assert len(DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES) >= 8
    assert len(DEFAULT_LITERATURE_GROUPS) >= 6
    assert len(DEFAULT_WORKFLOW_NARRATIVES) >= 12
    assert len(DEFAULT_KNOWN_PROBLEM_REGISTRY) >= 3
    assert len(DEFAULT_SCIENTIFIC_RULE_REFERENCES) >= 5


def test_grounding_registries_avoid_vague_internal_notes() -> None:
    registries = (
        DEFAULT_CITATION_REGISTRY,
        DEFAULT_BENCHMARK_MANIFESTS,
        DEFAULT_CORPUS_MANIFESTS,
        DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
        DEFAULT_LITERATURE_GROUPS,
        DEFAULT_WORKFLOW_NARRATIVES,
        DEFAULT_KNOWN_PROBLEM_REGISTRY,
        DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    )
    offending_entries: list[str] = []

    for registry in registries:
        for entry in registry:
            rendered = entry.model_dump_json().lower()
            if any(phrase in rendered for phrase in VAGUE_GROUNDING_PHRASES):
                offending_entries.append(
                    entry.model_dump().get("citation_id", repr(entry))
                )

    assert offending_entries == []


def test_workflow_briefings_stay_grounded_for_every_family() -> None:
    for workflow_family in KnowledgeWorkflowFamily:
        briefing = build_workflow_reference_briefing(workflow_family)
        expected_problem_count = len(
            {*briefing.evidence_claim.problem_ids, *briefing.limitation.problem_ids}
        )

        assert briefing.benchmark_manifest.primary_citation_ids
        assert briefing.evidence_claim.citation_ids
        assert briefing.limitation.citation_ids
        assert briefing.scientific_context
        assert briefing.literature_groups
        assert briefing.scientific_rules
        assert len(briefing.known_problems) == expected_problem_count


def test_knowledge_root_does_not_reexport_runtime_style_plumbing() -> None:
    forbidden_attributes = (
        "AssayResultIngestionAdapter",
        "LiteratureIngestionAdapter",
        "ManualEvidenceNoteAdapter",
        "StructureAnnotationIngestionAdapter",
        "EvidenceBundleRepository",
        "EvidenceClaimRepository",
        "ClaimResolutionRepository",
        "EvidenceRecordRepository",
    )

    assert not any(hasattr(knowledge, attribute) for attribute in forbidden_attributes)
