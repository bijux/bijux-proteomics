from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.package_graph import (
    WorkspacePackageGraph,
    build_workspace_package_graph,
)

__all__ = [
    "IntegrationPattern",
    "IntegrationPatternValidation",
    "accepted_integration_patterns",
    "validate_integration_patterns",
]


@dataclass(frozen=True)
class IntegrationPattern:
    """Accepted cross-package integration pattern."""

    pattern_id: str
    source_package: str
    target_package: str
    handoff_mode: str
    required_edges: tuple[tuple[str, str], ...]
    forbidden_edges: tuple[tuple[str, str], ...]
    rationale: str


@dataclass(frozen=True)
class IntegrationPatternValidation:
    """Validation result for one integration pattern."""

    pattern: IntegrationPattern
    valid: bool
    notes: tuple[str, ...]


def accepted_integration_patterns() -> tuple[IntegrationPattern, ...]:
    """Return the accepted package family integration patterns."""
    return (
        IntegrationPattern(
            pattern_id="runtime-to-core",
            source_package="bijux-proteomics-runtime",
            target_package="bijux-proteomics-core",
            handoff_mode="direct_dependency",
            required_edges=(("bijux-proteomics-runtime", "bijux-proteomics-core"),),
            forbidden_edges=(("bijux-proteomics-core", "bijux-proteomics-runtime"),),
            rationale="runtime may call canonical core logic directly, but core must not grow orchestration knowledge",
        ),
        IntegrationPattern(
            pattern_id="core-to-knowledge",
            source_package="bijux-proteomics-core",
            target_package="bijux-proteomics-knowledge",
            handoff_mode="artifact_handoff",
            required_edges=(),
            forbidden_edges=(
                ("bijux-proteomics-core", "bijux-proteomics-knowledge"),
                ("bijux-proteomics-knowledge", "bijux-proteomics-core"),
            ),
            rationale="core outputs should cross into knowledge as stable artifacts rather than direct package imports",
        ),
        IntegrationPattern(
            pattern_id="intelligence-to-lab",
            source_package="bijux-proteomics-intelligence",
            target_package="bijux-proteomics-lab",
            handoff_mode="artifact_handoff",
            required_edges=(),
            forbidden_edges=(
                ("bijux-proteomics-intelligence", "bijux-proteomics-lab"),
                ("bijux-proteomics-lab", "bijux-proteomics-intelligence"),
            ),
            rationale="lab execution planning should consume bounded outputs instead of importing intelligence internals directly",
        ),
    )


def _edge_set(graph: WorkspacePackageGraph) -> set[tuple[str, str]]:
    return {
        (edge.depender_package, edge.dependee_package)
        for edge in graph.dependency_edges
    }


def _validate_pattern(
    graph: WorkspacePackageGraph,
    pattern: IntegrationPattern,
) -> IntegrationPatternValidation:
    edges = _edge_set(graph)
    notes: list[str] = []
    for required in pattern.required_edges:
        if required in edges:
            notes.append(
                f"required edge {required[0]} -> {required[1]} is present for {pattern.handoff_mode}"
            )
        else:
            notes.append(f"missing required edge {required[0]} -> {required[1]}")
    for forbidden in pattern.forbidden_edges:
        if forbidden in edges:
            notes.append(f"forbidden edge {forbidden[0]} -> {forbidden[1]} is present")
        else:
            notes.append(f"forbidden edge {forbidden[0]} -> {forbidden[1]} is absent")
    valid = all(required in edges for required in pattern.required_edges) and all(
        forbidden not in edges for forbidden in pattern.forbidden_edges
    )
    notes.append(pattern.rationale)
    return IntegrationPatternValidation(
        pattern=pattern,
        valid=valid,
        notes=tuple(notes),
    )


def validate_integration_patterns(
    repo_root: Path,
) -> tuple[IntegrationPatternValidation, ...]:
    """Validate the accepted integration patterns against the package graph."""
    graph = build_workspace_package_graph(repo_root)
    return tuple(
        _validate_pattern(graph, pattern) for pattern in accepted_integration_patterns()
    )
