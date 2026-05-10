from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.dependencies.package_dependency_policy import (
    build_package_dependency_policy_report,
)
from bijux_proteomics_dev.governance.foundation.repository_product_shape import (
    REPOSITORY_PRODUCT_SHAPE_PATH,
    build_repository_product_shape_report,
)
from bijux_proteomics_dev.governance.package_shape.public_surfaces import (
    default_public_surface_contracts,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PackageBoundaryCoherenceIssue",
    "build_package_boundary_coherence_issues",
    "validate_package_boundary_coherence",
]


@dataclass(frozen=True)
class PackageBoundaryCoherenceIssue:
    """One mismatch across package role docs, public imports, and dependency rules."""

    code: str
    detail: str


def build_package_boundary_coherence_issues(
    repo_root: Path = REPO_ROOT,
) -> tuple[PackageBoundaryCoherenceIssue, ...]:
    """Build the boundary coherence issues for publishable packages."""

    report = build_repository_product_shape_report()
    policy_by_package = {
        entry.distribution_name: entry
        for entry in build_package_dependency_policy_report().entries
    }
    public_surface_by_package = {
        entry.distribution_name: entry for entry in default_public_surface_contracts()
    }
    runtime_public_surface = public_surface_by_package.get("bijux-proteomics-runtime")
    issues: list[PackageBoundaryCoherenceIssue] = []

    if not REPOSITORY_PRODUCT_SHAPE_PATH.exists():
        issues.append(
            PackageBoundaryCoherenceIssue(
                code="missing-owner-map",
                detail="repository product shape must exist before boundary coherence can run",
            )
        )
        return tuple(issues)

    for package in report.packages:
        readme_text = (repo_root / package.readme_path).read_text(encoding="utf-8")
        normalized_readme = " ".join(readme_text.split())
        normalized_summary = " ".join(package.role_summary.split())
        if normalized_summary not in normalized_readme:
            issues.append(
                PackageBoundaryCoherenceIssue(
                    code="readme-role-summary-drift",
                    detail=(
                        f"{package.distribution_name} README no longer states the "
                        f"declared role summary {package.role_summary!r}"
                    ),
                )
            )
        if (
            "Product architecture"
            not in readme_text
            or "Cross-package ownership" not in readme_text
        ):
            issues.append(
                PackageBoundaryCoherenceIssue(
                    code="readme-missing-root-routing",
                    detail=(
                        f"{package.distribution_name} README must route readers to "
                        "the product architecture and cross-package ownership pages"
                    ),
                )
            )

        public_surface = public_surface_by_package.get(package.distribution_name)
        if public_surface is None:
            issues.append(
                PackageBoundaryCoherenceIssue(
                    code="missing-public-surface-contract",
                    detail=(
                        f"{package.distribution_name} is missing a declared public "
                        "surface contract"
                    ),
                )
            )
        elif package.role_kind == "compatibility":
            expected_attributes = (
                runtime_public_surface.supported_attributes
                if (
                    runtime_public_surface is not None
                    and package.distribution_name == "agentic-proteins"
                )
                else ("__version__",)
            )
            if public_surface.supported_attributes != expected_attributes:
                issues.append(
                    PackageBoundaryCoherenceIssue(
                        code="compatibility-root-overgrowth",
                        detail=(
                            f"{package.distribution_name} root import surface must "
                            "stay compatibility-thin"
                        ),
                    )
                )
        elif (
            not public_surface.supported_attributes
            and not public_surface.supported_modules
        ):
            issues.append(
                PackageBoundaryCoherenceIssue(
                    code="empty-public-surface-contract",
                    detail=(
                        f"{package.distribution_name} must declare at least one "
                        "supported import surface"
                    ),
                )
            )

        policy_entry = policy_by_package[package.distribution_name]
        if policy_entry.allowed_outbound_edges != package.allowed_outbound_imports:
            issues.append(
                PackageBoundaryCoherenceIssue(
                    code="dependency-policy-drift",
                    detail=(
                        f"{package.distribution_name} allowed outbound imports no "
                        "longer match the repository product shape"
                    ),
                )
            )

    return tuple(issues)


def validate_package_boundary_coherence(
    repo_root: Path = REPO_ROOT,
) -> tuple[PackageBoundaryCoherenceIssue, ...]:
    """Validate cross-package coherence across docs, imports, and dependency rules."""

    return tuple(
        sorted(
            build_package_boundary_coherence_issues(repo_root),
            key=lambda issue: (issue.code, issue.detail),
        )
    )
