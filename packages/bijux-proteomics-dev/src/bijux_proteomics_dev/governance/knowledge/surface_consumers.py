from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.foundation.root_consumers import (
    DownstreamPackage,
    REPO_ROOT,
    downstream_packages,
)

__all__ = [
    "KNOWLEDGE_SURFACE_CONSUMERS_PATH",
    "KnowledgeSurfaceConsumerEntry",
    "build_knowledge_surface_consumers",
    "knowledge_surfaces",
    "run",
]


@dataclass(frozen=True)
class PublicKnowledgeSurface:
    """One durable knowledge import surface that downstream packages may consume."""

    module_name: str


@dataclass(frozen=True)
class KnowledgeSurfaceConsumerEntry:
    """One knowledge surface and the downstream packages that import it."""

    module_name: str
    consumer_distributions: tuple[str, ...]
    consumer_modules: tuple[str, ...]
    imported_symbols: tuple[str, ...]


KNOWLEDGE_SURFACE_CONSUMERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-surface-consumers.toml"
)


def knowledge_surfaces() -> tuple[PublicKnowledgeSurface, ...]:
    """Return durable knowledge surfaces that matter to downstream consumers."""

    return (
        PublicKnowledgeSurface("bijux_proteomics_knowledge"),
        PublicKnowledgeSurface("bijux_proteomics_knowledge.references"),
        PublicKnowledgeSurface(
            "bijux_proteomics_knowledge.references.workflows.benchmarks"
        ),
        PublicKnowledgeSurface(
            "bijux_proteomics_knowledge.references.workflows.briefings"
        ),
        PublicKnowledgeSurface(
            "bijux_proteomics_knowledge.references.grounding.ontologies"
        ),
        PublicKnowledgeSurface("bijux_proteomics_knowledge.references.grounding.rules"),
        PublicKnowledgeSurface(
            "bijux_proteomics_knowledge.references.workflows.lookups"
        ),
        PublicKnowledgeSurface("bijux_proteomics_knowledge.memory.models.claims"),
        PublicKnowledgeSurface("bijux_proteomics_knowledge.memory.models.evidence"),
        PublicKnowledgeSurface("bijux_proteomics_knowledge.memory.integrity.graph"),
        PublicKnowledgeSurface(
            "bijux_proteomics_knowledge.memory.normalization.ingestion"
        ),
        PublicKnowledgeSurface(
            "bijux_proteomics_knowledge.memory.reconciliation.resolution"
        ),
        PublicKnowledgeSurface("bijux_proteomics_knowledge.reviews.packets"),
    )


def _downstream_source_packages() -> tuple[DownstreamPackage, ...]:
    return tuple(
        package
        for package in downstream_packages()
        if package.distribution_name != "bijux-proteomics-knowledge"
    )


def _src_root(package: DownstreamPackage) -> Path:
    return (
        REPO_ROOT / "packages" / package.distribution_name / "src" / package.import_root
    )


def build_knowledge_surface_consumers() -> tuple[KnowledgeSurfaceConsumerEntry, ...]:
    """Build the checked downstream consumer map for durable knowledge surfaces."""

    surfaces = knowledge_surfaces()
    modules = {surface.module_name for surface in surfaces}
    consumers_by_surface: dict[str, set[str]] = {
        module_name: set() for module_name in modules
    }
    distributions_by_surface: dict[str, set[str]] = {
        module_name: set() for module_name in modules
    }
    symbols_by_surface: dict[str, set[str]] = {
        module_name: set() for module_name in modules
    }

    for package in _downstream_source_packages():
        src_root = _src_root(package)
        if not src_root.exists():
            continue
        for path in src_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in modules:
                            continue
                        distributions_by_surface[alias.name].add(
                            package.distribution_name
                        )
                        consumers_by_surface[alias.name].add(relative_path)
                if not isinstance(node, ast.ImportFrom) or node.module is None:
                    continue
                if node.module not in modules:
                    continue
                distributions_by_surface[node.module].add(package.distribution_name)
                consumers_by_surface[node.module].add(relative_path)
                for alias in node.names:
                    symbols_by_surface[node.module].add(alias.name)

    return tuple(
        KnowledgeSurfaceConsumerEntry(
            module_name=surface.module_name,
            consumer_distributions=tuple(
                sorted(distributions_by_surface[surface.module_name])
            ),
            consumer_modules=tuple(sorted(consumers_by_surface[surface.module_name])),
            imported_symbols=tuple(sorted(symbols_by_surface[surface.module_name])),
        )
        for surface in surfaces
    )


def _toml_text(entries: tuple[KnowledgeSurfaceConsumerEntry, ...]) -> str:
    lines = [
        "# Generated knowledge surface consumer matrix.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.knowledge.surface_consumers",
        "",
    ]
    for entry in entries:
        distributions = ", ".join(
            f'"{value}"' for value in entry.consumer_distributions
        )
        modules = ", ".join(f'"{value}"' for value in entry.consumer_modules)
        symbols = ", ".join(f'"{value}"' for value in entry.imported_symbols)
        lines.extend(
            [
                "[[surface]]",
                f'name = "{entry.module_name}"',
                f"consumer_count = {len(entry.consumer_modules)}",
                f"consumer_distributions = [{distributions}]",
                f"consumer_modules = [{modules}]",
                f"imported_symbols = [{symbols}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[KnowledgeSurfaceConsumerEntry, ...]) -> bool:
    if not KNOWLEDGE_SURFACE_CONSUMERS_PATH.exists():
        return False
    return KNOWLEDGE_SURFACE_CONSUMERS_PATH.read_text(encoding="utf-8") == _toml_text(
        entries
    )


def run(check: bool = False) -> int:
    entries = build_knowledge_surface_consumers()
    if check:
        if _is_up_to_date(entries):
            print("knowledge surface consumer matrix is up to date")
            return 0
        print("knowledge surface consumer matrix is stale; regenerate it")
        return 1
    KNOWLEDGE_SURFACE_CONSUMERS_PATH.write_text(
        _toml_text(entries),
        encoding="utf-8",
    )
    print("generated knowledge surface consumer matrix")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the knowledge surface consumer matrix."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the consumer matrix is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
