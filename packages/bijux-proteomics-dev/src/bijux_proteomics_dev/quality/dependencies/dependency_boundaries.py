from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.graphs.package_graph import (
    WorkspacePackage,
    load_workspace_packages,
)

__all__ = [
    "DependencyBoundaryPolicy",
    "DependencyBoundaryViolation",
    "default_dependency_boundary_policies",
    "evaluate_dependency_boundary_policy",
    "validate_workspace_dependency_boundaries",
]


@dataclass(frozen=True)
class DependencyBoundaryPolicy:
    """Package-specific external dependency minimization policy."""

    package_name: str
    max_external_dependencies: int
    forbidden_external_dependencies: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class DependencyBoundaryViolation:
    """One dependency boundary violation."""

    package_name: str
    code: str
    detail: str


def default_dependency_boundary_policies() -> tuple[DependencyBoundaryPolicy, ...]:
    """Return the repository dependency minimization policy set."""
    heavy_science = (
        "biopython",
        "einops",
        "huggingface-hub",
        "langchain-community",
        "langchain-core",
        "langchain-huggingface",
        "langchain-text-splitters",
        "langsmith",
        "numpy",
        "openprotein-python",
        "pyarrow",
        "requests",
        "slowapi",
        "tokenizers",
        "torch",
        "transformers",
        "uvicorn",
    )
    return (
        DependencyBoundaryPolicy(
            package_name="agentic-proteins",
            max_external_dependencies=0,
            forbidden_external_dependencies=heavy_science,
            rationale="compatibility forwarding stays narrow when it only depends on canonical workspace packages",
        ),
        DependencyBoundaryPolicy(
            package_name="bijux-proteomics-foundation",
            max_external_dependencies=1,
            forbidden_external_dependencies=heavy_science,
            rationale="foundation should stay close to shared schema and serialization primitives",
        ),
        DependencyBoundaryPolicy(
            package_name="bijux-proteomics-knowledge",
            max_external_dependencies=1,
            forbidden_external_dependencies=heavy_science,
            rationale="knowledge should not quietly pick up runtime or heavy scientific stack pressure",
        ),
        DependencyBoundaryPolicy(
            package_name="bijux-proteomics-lab",
            max_external_dependencies=1,
            forbidden_external_dependencies=heavy_science,
            rationale="lab planning should stay mostly inside canonical workspace contracts",
        ),
    )


def evaluate_dependency_boundary_policy(
    package: WorkspacePackage,
    policy: DependencyBoundaryPolicy,
) -> tuple[DependencyBoundaryViolation, ...]:
    """Evaluate one package against its external dependency boundary."""
    violations: list[DependencyBoundaryViolation] = []
    external_dependencies = set(package.external_dependencies)
    if len(external_dependencies) > policy.max_external_dependencies:
        violations.append(
            DependencyBoundaryViolation(
                package_name=package.package_name,
                code="external-dependency-budget-exceeded",
                detail=(
                    f"{package.package_name} declares {len(external_dependencies)} external dependencies, "
                    f"exceeding the budget of {policy.max_external_dependencies}"
                ),
            )
        )
    forbidden = sorted(
        external_dependencies.intersection(policy.forbidden_external_dependencies)
    )
    if forbidden:
        violations.append(
            DependencyBoundaryViolation(
                package_name=package.package_name,
                code="forbidden-heavy-dependency",
                detail=(
                    f"{package.package_name} depends on forbidden heavy packages {forbidden}: "
                    f"{policy.rationale}"
                ),
            )
        )
    return tuple(violations)


def validate_workspace_dependency_boundaries(
    repo_root: Path,
) -> tuple[DependencyBoundaryViolation, ...]:
    """Validate package-specific external dependency boundaries across the repo."""
    packages = {
        package.package_name: package for package in load_workspace_packages(repo_root)
    }
    violations: list[DependencyBoundaryViolation] = []
    for policy in default_dependency_boundary_policies():
        package = packages[policy.package_name]
        violations.extend(evaluate_dependency_boundary_policy(package, policy))
    return tuple(
        sorted(
            violations, key=lambda violation: (violation.package_name, violation.code)
        )
    )
