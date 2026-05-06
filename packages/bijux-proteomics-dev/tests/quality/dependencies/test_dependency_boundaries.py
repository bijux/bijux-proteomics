from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.dependencies.dependency_boundaries import (
    DependencyBoundaryPolicy,
    evaluate_dependency_boundary_policy,
    validate_workspace_dependency_boundaries,
)
from bijux_proteomics_dev.quality.graphs.package_graph import WorkspacePackage

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def _package(*, name: str, external_dependencies: tuple[str, ...]) -> WorkspacePackage:
    root = Path("/tmp") / name
    return WorkspacePackage(
        package_name=name,
        distribution_name=name,
        import_root=name.replace("-", "_"),
        package_dir=root,
        pyproject_path=root / "pyproject.toml",
        readme_path=root / "README.md",
        src_dir=root / "src",
        tests_dir=root / "tests",
        layer_index=0,
        workspace_dependencies=(),
        external_dependencies=external_dependencies,
    )


def test_workspace_dependency_boundaries_match_current_packages() -> None:
    assert validate_workspace_dependency_boundaries(REPO_ROOT) == ()


def test_dependency_boundary_policy_rejects_heavy_dependencies_and_budget_growth() -> (
    None
):
    policy = DependencyBoundaryPolicy(
        package_name="bijux-proteomics-foundation",
        max_external_dependencies=1,
        forbidden_external_dependencies=("numpy", "torch"),
        rationale="foundation should stay minimal",
    )

    violations = evaluate_dependency_boundary_policy(
        _package(
            name="bijux-proteomics-foundation",
            external_dependencies=("pydantic", "numpy"),
        ),
        policy,
    )

    codes = {violation.code for violation in violations}
    assert codes == {
        "external-dependency-budget-exceeded",
        "forbidden-heavy-dependency",
    }
