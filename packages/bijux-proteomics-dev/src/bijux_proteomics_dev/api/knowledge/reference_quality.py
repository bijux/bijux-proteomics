from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.foundation.root_consumers import REPO_ROOT
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
    list_workflow_reference_briefings,
)
from bijux_proteomics_knowledge.references.grounding.citations import DEFAULT_CITATION_REGISTRY
from bijux_proteomics_knowledge.references.grounding.contexts import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
)
from bijux_proteomics_knowledge.references.grounding.corpora import DEFAULT_CORPUS_MANIFESTS
from bijux_proteomics_knowledge.references.grounding.literature import DEFAULT_LITERATURE_GROUPS
from bijux_proteomics_knowledge.references.workflows.narratives import DEFAULT_WORKFLOW_NARRATIVES
from bijux_proteomics_knowledge.references.grounding.ontologies import DEFAULT_ONTOLOGY_MAPPINGS
from bijux_proteomics_knowledge.references.grounding.problems import DEFAULT_KNOWN_PROBLEM_REGISTRY
from bijux_proteomics_knowledge.references.grounding.rules import DEFAULT_SCIENTIFIC_RULE_REFERENCES

__all__ = [
    "KNOWLEDGE_ORPHAN_REFERENCES_PATH",
    "KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH",
    "KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH",
    "KnowledgeOrphanReferenceEntry",
    "KnowledgeProvenanceSurfaceEntry",
    "KnowledgeUnderCuratedWorkflowEntry",
    "build_knowledge_orphan_reference_report",
    "build_knowledge_provenance_completeness_report",
    "build_knowledge_under_curated_workflow_report",
    "run",
]


@dataclass(frozen=True)
class KnowledgeProvenanceSurfaceEntry:
    """One knowledge reference surface and its provenance-completeness status."""

    surface_name: str
    entry_count: int
    complete_entry_count: int
    required_fields: tuple[str, ...]
    incomplete_entry_ids: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeUnderCuratedWorkflowEntry:
    """One workflow family and the coverage gaps that still keep curation shallow."""

    workflow_family: str
    benchmark_count: int
    narrative_count: int
    scientific_context_count: int
    literature_group_count: int
    known_problem_count: int
    scientific_rule_count: int
    scope_limit_note_count: int
    under_curated_reasons: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeOrphanReferenceEntry:
    """One registry surface and the reference identifiers that nothing else uses."""

    surface_name: str
    entry_count: int
    orphan_ids: tuple[str, ...]


KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-provenance-completeness.toml"
)
KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-under-curated-workflows.toml"
)
KNOWLEDGE_ORPHAN_REFERENCES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-orphan-references.toml"
)


def _entry_id(entry: object) -> str:
    for field_name in (
        "citation_id",
        "benchmark_id",
        "corpus_id",
        "context_id",
        "group_id",
        "narrative_id",
        "problem_id",
        "rule_id",
        "term_id",
    ):
        value = getattr(entry, field_name, None)
        if isinstance(value, str):
            return value
    raise RuntimeError(f"Unable to resolve stable identifier for {type(entry)!r}")


def _present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, tuple | list | set | dict):
        return bool(value)
    return True


def build_knowledge_provenance_completeness_report() -> tuple[KnowledgeProvenanceSurfaceEntry, ...]:
    """Measure provenance completeness across curated knowledge reference surfaces."""

    surfaces: tuple[tuple[str, tuple[object, ...], tuple[str, ...]], ...] = (
        (
            "citations",
            DEFAULT_CITATION_REGISTRY,
            (
                "title",
                "source_kind",
                "venue",
                "publisher",
                "source_locator_kind",
                "access_route",
                "publication_year",
                "source_version",
                "retrieval_trace",
                "evidence_role",
                "license_note",
                "summary",
            ),
        ),
        (
            "benchmarks",
            DEFAULT_BENCHMARK_MANIFESTS,
            (
                "dataset_id",
                "dataset_locator",
                "primary_citation_ids",
                "corpus_ids",
                "benchmark_rationale",
                "version_trace",
                "retrieval_trace",
                "dataset_license_and_reuse_note",
                "reproduction_requirements",
                "comparison_notes",
                "exclusion_notes",
                "weakness_notes",
                "failure_mode_notes",
            ),
        ),
        (
            "corpora",
            DEFAULT_CORPUS_MANIFESTS,
            (
                "format_family",
                "scientific_scope",
                "source_version",
                "version_trace",
                "retrieval_trace",
                "license_and_reuse_note",
                "benchmark_ids",
            ),
        ),
        (
            "contexts",
            DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
            (
                "scientific_assertion",
                "interpretation_caveat",
                "version_trace",
                "retrieval_trace",
                "citation_ids",
                "benchmark_ids",
            ),
        ),
        (
            "literature_groups",
            DEFAULT_LITERATURE_GROUPS,
            (
                "curation_note",
                "version_trace",
                "retrieval_trace",
                "citation_ids",
                "benchmark_ids",
            ),
        ),
        (
            "narratives",
            DEFAULT_WORKFLOW_NARRATIVES,
            (
                "narrative_text",
                "version_trace",
                "retrieval_trace",
                "benchmark_ids",
                "citation_ids",
                "scope_limit_notes",
            ),
        ),
        (
            "ontology_mappings",
            DEFAULT_ONTOLOGY_MAPPINGS,
            (
                "preferred_label",
                "normalized_key",
                "source_name",
                "version_trace",
                "retrieval_trace",
                "citation_ids",
            ),
        ),
        (
            "known_problems",
            DEFAULT_KNOWN_PROBLEM_REGISTRY,
            (
                "problem_summary",
                "mitigation_guidance",
                "version_trace",
                "retrieval_trace",
                "affected_workflow_families",
                "affected_benchmark_ids",
                "citation_ids",
            ),
        ),
        (
            "scientific_rules",
            DEFAULT_SCIENTIFIC_RULE_REFERENCES,
            (
                "rule_statement",
                "version_trace",
                "retrieval_trace",
                "citation_ids",
                "benchmark_ids",
                "benchmark_rationale",
            ),
        ),
    )

    entries: list[KnowledgeProvenanceSurfaceEntry] = []
    for surface_name, registry, required_fields in surfaces:
        incomplete_entry_ids: list[str] = []
        for entry in registry:
            missing_fields = [
                field_name
                for field_name in required_fields
                if not _present(getattr(entry, field_name))
            ]
            if surface_name == "corpora":
                has_location = _present(getattr(entry, "repo_relative_path")) or _present(
                    getattr(entry, "reference_locator")
                )
                if not has_location:
                    missing_fields.append("repo_relative_path|reference_locator")
            if surface_name == "citations":
                has_locator = _present(getattr(entry, "doi")) or _present(
                    getattr(entry, "url")
                )
                if not has_locator:
                    missing_fields.append("doi|url")
            if missing_fields:
                incomplete_entry_ids.append(_entry_id(entry))
        entries.append(
            KnowledgeProvenanceSurfaceEntry(
                surface_name=surface_name,
                entry_count=len(registry),
                complete_entry_count=len(registry) - len(incomplete_entry_ids),
                required_fields=required_fields,
                incomplete_entry_ids=tuple(sorted(incomplete_entry_ids)),
            )
        )
    return tuple(entries)


def build_knowledge_under_curated_workflow_report() -> tuple[KnowledgeUnderCuratedWorkflowEntry, ...]:
    """Measure which workflow families still have shallower surrounding curation."""

    entries: list[KnowledgeUnderCuratedWorkflowEntry] = []
    for workflow_family in KnowledgeWorkflowFamily:
        briefing = build_workflow_reference_briefing(workflow_family)
        benchmark_count = sum(
            1
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.workflow_family is workflow_family
        )
        narrative_count = sum(
            1
            for narrative in DEFAULT_WORKFLOW_NARRATIVES
            if narrative.workflow_family is workflow_family
        )
        reasons: list[str] = []
        if len(briefing.scientific_context) < 2:
            reasons.append("fewer than two scientific context entries")
        if len(briefing.literature_groups) < 2:
            reasons.append("fewer than two literature groups")
        if len(briefing.known_problems) < 1:
            reasons.append("no known problem entry")
        if len(briefing.scientific_rules) < 2:
            reasons.append("fewer than two scientific rules")
        entries.append(
            KnowledgeUnderCuratedWorkflowEntry(
                workflow_family=workflow_family.value,
                benchmark_count=benchmark_count,
                narrative_count=narrative_count,
                scientific_context_count=len(briefing.scientific_context),
                literature_group_count=len(briefing.literature_groups),
                known_problem_count=len(briefing.known_problems),
                scientific_rule_count=len(briefing.scientific_rules),
                scope_limit_note_count=len(briefing.scope_limit_notes),
                under_curated_reasons=tuple(reasons),
            )
        )
    return tuple(entries)


def build_knowledge_orphan_reference_report() -> tuple[KnowledgeOrphanReferenceEntry, ...]:
    """Report curated references that no other knowledge surface currently uses."""

    citation_refs: set[str] = set()
    corpus_refs: set[str] = set()
    context_refs: set[str] = set()
    problem_refs: set[str] = set()
    benchmark_refs: set[str] = set()
    rule_refs: set[str] = set()
    literature_group_refs = {
        group.group_id
        for briefing in list_workflow_reference_briefings()
        for group in briefing.literature_groups
    }

    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        citation_refs.update(manifest.primary_citation_ids)
        corpus_refs.update(manifest.corpus_ids)
        benchmark_refs.add(manifest.benchmark_id)
    for narrative in DEFAULT_WORKFLOW_NARRATIVES:
        citation_refs.update(narrative.citation_ids)
        context_refs.update(narrative.context_ids)
        problem_refs.update(narrative.problem_ids)
        benchmark_refs.update(narrative.benchmark_ids)
    for context in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES:
        citation_refs.update(context.citation_ids)
        benchmark_refs.update(context.benchmark_ids)
        rule_refs.update(context.related_rule_ids)
    for literature_group in DEFAULT_LITERATURE_GROUPS:
        citation_refs.update(literature_group.citation_ids)
        benchmark_refs.update(literature_group.benchmark_ids)
        context_refs.update(literature_group.context_ids)
    for problem in DEFAULT_KNOWN_PROBLEM_REGISTRY:
        citation_refs.update(problem.citation_ids)
        corpus_refs.update(problem.affected_corpus_ids)
        benchmark_refs.update(problem.affected_benchmark_ids)
    for scientific_rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES:
        citation_refs.update(scientific_rule.citation_ids)
        benchmark_refs.update(scientific_rule.benchmark_ids)
    for corpus in DEFAULT_CORPUS_MANIFESTS:
        citation_refs.update(corpus.citation_ids)
        benchmark_refs.update(corpus.benchmark_ids)
    for mapping in DEFAULT_ONTOLOGY_MAPPINGS:
        citation_refs.update(mapping.citation_ids)

    return (
        KnowledgeOrphanReferenceEntry(
            surface_name="citations",
            entry_count=len(DEFAULT_CITATION_REGISTRY),
            orphan_ids=tuple(
                sorted(
                    citation.citation_id
                    for citation in DEFAULT_CITATION_REGISTRY
                    if citation.citation_id not in citation_refs
                )
            ),
        ),
        KnowledgeOrphanReferenceEntry(
            surface_name="benchmarks",
            entry_count=len(DEFAULT_BENCHMARK_MANIFESTS),
            orphan_ids=tuple(
                sorted(
                    manifest.benchmark_id
                    for manifest in DEFAULT_BENCHMARK_MANIFESTS
                    if manifest.benchmark_id not in benchmark_refs
                )
            ),
        ),
        KnowledgeOrphanReferenceEntry(
            surface_name="corpora",
            entry_count=len(DEFAULT_CORPUS_MANIFESTS),
            orphan_ids=tuple(
                sorted(
                    corpus.corpus_id
                    for corpus in DEFAULT_CORPUS_MANIFESTS
                    if corpus.corpus_id not in corpus_refs
                )
            ),
        ),
        KnowledgeOrphanReferenceEntry(
            surface_name="scientific_context",
            entry_count=len(DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES),
            orphan_ids=tuple(
                sorted(
                    context.context_id
                    for context in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES
                    if context.context_id not in context_refs
                )
            ),
        ),
        KnowledgeOrphanReferenceEntry(
            surface_name="known_problems",
            entry_count=len(DEFAULT_KNOWN_PROBLEM_REGISTRY),
            orphan_ids=tuple(
                sorted(
                    problem.problem_id
                    for problem in DEFAULT_KNOWN_PROBLEM_REGISTRY
                    if problem.problem_id not in problem_refs
                )
            ),
        ),
        KnowledgeOrphanReferenceEntry(
            surface_name="literature_groups",
            entry_count=len(DEFAULT_LITERATURE_GROUPS),
            orphan_ids=tuple(
                sorted(
                    group.group_id
                    for group in DEFAULT_LITERATURE_GROUPS
                    if group.group_id not in literature_group_refs
                )
            ),
        ),
        KnowledgeOrphanReferenceEntry(
            surface_name="scientific_rules",
            entry_count=len(DEFAULT_SCIENTIFIC_RULE_REFERENCES),
            orphan_ids=tuple(
                sorted(
                    scientific_rule.rule_id
                    for scientific_rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES
                    if scientific_rule.rule_id not in rule_refs
                )
            ),
        ),
    )


def _provenance_toml_text(entries: tuple[KnowledgeProvenanceSurfaceEntry, ...]) -> str:
    lines = [
        "# Generated knowledge provenance completeness report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.knowledge.reference_quality",
        "",
    ]
    for entry in entries:
        required_fields = ", ".join(f'"{value}"' for value in entry.required_fields)
        incomplete_ids = ", ".join(f'"{value}"' for value in entry.incomplete_entry_ids)
        lines.extend(
            [
                "[[surface]]",
                f'name = "{entry.surface_name}"',
                f"entry_count = {entry.entry_count}",
                f"complete_entry_count = {entry.complete_entry_count}",
                f"required_fields = [{required_fields}]",
                f"incomplete_entry_ids = [{incomplete_ids}]",
                "",
            ]
        )
    return "\n".join(lines)


def _under_curated_toml_text(entries: tuple[KnowledgeUnderCuratedWorkflowEntry, ...]) -> str:
    lines = [
        "# Generated knowledge under-curated workflow report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.knowledge.reference_quality",
        "",
    ]
    for entry in entries:
        reasons = ", ".join(f'"{value}"' for value in entry.under_curated_reasons)
        lines.extend(
            [
                "[[workflow]]",
                f'family = "{entry.workflow_family}"',
                f"benchmark_count = {entry.benchmark_count}",
                f"narrative_count = {entry.narrative_count}",
                f"scientific_context_count = {entry.scientific_context_count}",
                f"literature_group_count = {entry.literature_group_count}",
                f"known_problem_count = {entry.known_problem_count}",
                f"scientific_rule_count = {entry.scientific_rule_count}",
                f"scope_limit_note_count = {entry.scope_limit_note_count}",
                f"under_curated_reasons = [{reasons}]",
                "",
            ]
        )
    return "\n".join(lines)


def _orphan_toml_text(entries: tuple[KnowledgeOrphanReferenceEntry, ...]) -> str:
    lines = [
        "# Generated knowledge orphan reference report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.knowledge.reference_quality",
        "",
    ]
    for entry in entries:
        orphan_ids = ", ".join(f'"{value}"' for value in entry.orphan_ids)
        lines.extend(
            [
                "[[surface]]",
                f'name = "{entry.surface_name}"',
                f"entry_count = {entry.entry_count}",
                f"orphan_count = {len(entry.orphan_ids)}",
                f"orphan_ids = [{orphan_ids}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date() -> bool:
    provenance_entries = build_knowledge_provenance_completeness_report()
    under_curated_entries = build_knowledge_under_curated_workflow_report()
    orphan_entries = build_knowledge_orphan_reference_report()
    return (
        KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH.exists()
        and KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH.exists()
        and KNOWLEDGE_ORPHAN_REFERENCES_PATH.exists()
        and KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH.read_text(encoding="utf-8")
        == _provenance_toml_text(provenance_entries)
        and KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH.read_text(encoding="utf-8")
        == _under_curated_toml_text(under_curated_entries)
        and KNOWLEDGE_ORPHAN_REFERENCES_PATH.read_text(encoding="utf-8")
        == _orphan_toml_text(orphan_entries)
    )


def run(check: bool = False) -> int:
    provenance_entries = build_knowledge_provenance_completeness_report()
    under_curated_entries = build_knowledge_under_curated_workflow_report()
    orphan_entries = build_knowledge_orphan_reference_report()
    if check:
        if _is_up_to_date():
            print("knowledge reference quality reports are up to date")
            return 0
        print("knowledge reference quality reports are stale; regenerate them")
        return 1
    KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH.write_text(
        _provenance_toml_text(provenance_entries),
        encoding="utf-8",
    )
    KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH.write_text(
        _under_curated_toml_text(under_curated_entries),
        encoding="utf-8",
    )
    KNOWLEDGE_ORPHAN_REFERENCES_PATH.write_text(
        _orphan_toml_text(orphan_entries),
        encoding="utf-8",
    )
    print("generated knowledge reference quality reports")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate knowledge provenance and curation reports."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the knowledge reference reports are not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
