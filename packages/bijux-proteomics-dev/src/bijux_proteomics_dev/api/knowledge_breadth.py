from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
)
from bijux_proteomics_knowledge.references.grounding.citations import DEFAULT_CITATION_REGISTRY
from bijux_proteomics_knowledge.references.grounding.contexts import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
)
from bijux_proteomics_knowledge.references.grounding.corpora import DEFAULT_CORPUS_MANIFESTS
from bijux_proteomics_knowledge.references.grounding.literature import DEFAULT_LITERATURE_GROUPS
from bijux_proteomics_knowledge.references.workflows.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
)
from bijux_proteomics_knowledge.references.grounding.ontologies import DEFAULT_ONTOLOGY_MAPPINGS
from bijux_proteomics_knowledge.references.grounding.problems import (
    DEFAULT_KNOWN_PROBLEM_REGISTRY,
)
from bijux_proteomics_knowledge.references.grounding.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
)

from bijux_proteomics_dev.api.foundation_root_consumers import REPO_ROOT

__all__ = [
    "KNOWLEDGE_BREADTH_PATH",
    "KnowledgeBreadthGuard",
    "KnowledgeBreadthMetrics",
    "KnowledgeBreadthReport",
    "build_knowledge_breadth_report",
    "run",
    "validate_knowledge_breadth",
]


KNOWLEDGE_BREADTH_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-breadth.toml"
)
KNOWLEDGE_ROOT_API_POLICY = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-root-api.toml"
)
KNOWLEDGE_REFERENCES_ROOT_API_POLICY = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "knowledge-references-root-api.toml"
)


@dataclass(frozen=True)
class KnowledgeBreadthMetrics:
    """Current knowledge menu breadth paired with curation depth."""

    root_public_symbol_count: int
    references_public_symbol_count: int
    total_public_surface_count: int
    query_helper_count: int
    curated_registry_entry_count: int
    curated_entries_per_public_surface: float
    curated_entries_per_query_helper: float


@dataclass(frozen=True)
class KnowledgeBreadthGuard:
    """Release-blocking guardrails for knowledge breadth growth."""

    baseline_total_public_surface_count: int
    baseline_query_helper_count: int
    baseline_curated_registry_entry_count: int
    baseline_curated_entries_per_public_surface: float
    baseline_curated_entries_per_query_helper: float


@dataclass(frozen=True)
class KnowledgeBreadthReport:
    """Checked knowledge breadth report."""

    metrics: KnowledgeBreadthMetrics
    guard: KnowledgeBreadthGuard


def _rounded_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 2)


def _curated_registry_entry_count() -> int:
    return sum(
        (
            len(DEFAULT_BENCHMARK_MANIFESTS),
            len(DEFAULT_CITATION_REGISTRY),
            len(DEFAULT_CORPUS_MANIFESTS),
            len(DEFAULT_KNOWN_PROBLEM_REGISTRY),
            len(DEFAULT_LITERATURE_GROUPS),
            len(DEFAULT_ONTOLOGY_MAPPINGS),
            len(DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES),
            len(DEFAULT_SCIENTIFIC_RULE_REFERENCES),
            len(DEFAULT_WORKFLOW_NARRATIVES),
        )
    )


def _public_symbol_count(path: Path) -> int:
    with path.open("rb") as handle:
        return len(tomllib.load(handle)["symbol"])


def build_knowledge_breadth_report() -> KnowledgeBreadthReport:
    """Build the checked report that pairs knowledge breadth with curation depth."""

    root_public_symbol_count = _public_symbol_count(KNOWLEDGE_ROOT_API_POLICY)
    references_public_symbol_count = _public_symbol_count(
        KNOWLEDGE_REFERENCES_ROOT_API_POLICY
    )
    total_public_surface_count = (
        root_public_symbol_count + references_public_symbol_count
    )
    query_helper_count = 1
    curated_registry_entry_count = _curated_registry_entry_count()
    metrics = KnowledgeBreadthMetrics(
        root_public_symbol_count=root_public_symbol_count,
        references_public_symbol_count=references_public_symbol_count,
        total_public_surface_count=total_public_surface_count,
        query_helper_count=query_helper_count,
        curated_registry_entry_count=curated_registry_entry_count,
        curated_entries_per_public_surface=_rounded_ratio(
            curated_registry_entry_count,
            total_public_surface_count,
        ),
        curated_entries_per_query_helper=_rounded_ratio(
            curated_registry_entry_count,
            query_helper_count,
        ),
    )
    return KnowledgeBreadthReport(
        metrics=metrics,
        guard=KnowledgeBreadthGuard(
            baseline_total_public_surface_count=metrics.total_public_surface_count,
            baseline_query_helper_count=metrics.query_helper_count,
            baseline_curated_registry_entry_count=metrics.curated_registry_entry_count,
            baseline_curated_entries_per_public_surface=(
                metrics.curated_entries_per_public_surface
            ),
            baseline_curated_entries_per_query_helper=(
                metrics.curated_entries_per_query_helper
            ),
        ),
    )


def validate_knowledge_breadth() -> tuple[str, ...]:
    """Fail release when knowledge menu breadth grows faster than curation depth."""

    report = build_knowledge_breadth_report()
    metrics = report.metrics
    guard = report.guard
    failures: list[str] = []

    if metrics.query_helper_count > guard.baseline_query_helper_count:
        failures.append(
            "knowledge broadened the query-helper menu beyond the governed single-helper surface"
        )
    if (
        metrics.curated_entries_per_public_surface
        < guard.baseline_curated_entries_per_public_surface
    ):
        failures.append(
            "knowledge public breadth now grows faster than curated reference depth"
        )
    if (
        metrics.curated_entries_per_query_helper
        < guard.baseline_curated_entries_per_query_helper
    ):
        failures.append(
            "knowledge query-helper breadth now grows faster than curated reference depth"
        )
    if metrics.total_public_surface_count > guard.baseline_total_public_surface_count:
        if (
            metrics.curated_registry_entry_count
            <= guard.baseline_curated_registry_entry_count
        ):
            failures.append(
                "knowledge public surface grew without adding deeper curated scientific memory"
            )
    return tuple(failures)


def _toml_text(report: KnowledgeBreadthReport) -> str:
    metrics = report.metrics
    guard = report.guard
    return "\n".join(
        (
            "# Generated knowledge breadth-versus-curation-depth report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.knowledge_breadth",
            "",
            "[metrics]",
            f"root_public_symbol_count = {metrics.root_public_symbol_count}",
            (
                "references_public_symbol_count = "
                f"{metrics.references_public_symbol_count}"
            ),
            f"total_public_surface_count = {metrics.total_public_surface_count}",
            f"query_helper_count = {metrics.query_helper_count}",
            f"curated_registry_entry_count = {metrics.curated_registry_entry_count}",
            (
                "curated_entries_per_public_surface = "
                f"{metrics.curated_entries_per_public_surface}"
            ),
            (
                "curated_entries_per_query_helper = "
                f"{metrics.curated_entries_per_query_helper}"
            ),
            "",
            "[guard]",
            (
                "baseline_total_public_surface_count = "
                f"{guard.baseline_total_public_surface_count}"
            ),
            (
                "baseline_query_helper_count = "
                f"{guard.baseline_query_helper_count}"
            ),
            (
                "baseline_curated_registry_entry_count = "
                f"{guard.baseline_curated_registry_entry_count}"
            ),
            (
                "baseline_curated_entries_per_public_surface = "
                f"{guard.baseline_curated_entries_per_public_surface}"
            ),
            (
                "baseline_curated_entries_per_query_helper = "
                f"{guard.baseline_curated_entries_per_query_helper}"
            ),
        )
    )


def _is_up_to_date(report: KnowledgeBreadthReport) -> bool:
    if not KNOWLEDGE_BREADTH_PATH.exists():
        return False
    return KNOWLEDGE_BREADTH_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_knowledge_breadth_report()
    failures = validate_knowledge_breadth()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("knowledge breadth report is up to date")
            return 0
        print("knowledge breadth report is stale; regenerate it")
        return 1
    KNOWLEDGE_BREADTH_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated knowledge breadth report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the knowledge breadth report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the knowledge breadth report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
