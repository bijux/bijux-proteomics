from __future__ import annotations

from bijux_proteomics_dev.quality.dependencies.core_dependency_minimization import (
    CORE_DEPENDENCY_MINIMIZATION_PATH,
    CoreDependencyMinimizationPolicy,
    CoreDependencyMinimizationRule,
    build_core_dependency_minimization_violations,
    evaluate_dependency_declarations,
    evaluate_source_imports,
    load_core_dependency_minimization_policy,
    run,
)


def _policy(*, allowed_optional_module_prefixes: tuple[str, ...] = ()) -> (
    CoreDependencyMinimizationPolicy
):
    return CoreDependencyMinimizationPolicy(
        package_name="bijux-proteomics-core",
        rules=(
            CoreDependencyMinimizationRule(
                distribution_name="pandas",
                forbidden_import_roots=("pandas",),
                allowed_optional_dependency_groups=(),
                allowed_optional_module_prefixes=allowed_optional_module_prefixes,
                rationale="core default imports must stay pandas-free",
            ),
        ),
    )


def test_core_dependency_minimization_manifest_is_repository_owned() -> None:
    assert CORE_DEPENDENCY_MINIMIZATION_PATH.as_posix().endswith(
        "configs/package-governance/core-dependency-minimization.toml"
    )


def test_core_dependency_minimization_manifest_covers_named_heavy_dependencies() -> (
    None
):
    policy = load_core_dependency_minimization_policy()

    assert policy.package_name == "bijux-proteomics-core"
    assert [rule.distribution_name for rule in policy.rules] == [
        "pandas",
        "scikit-learn",
        "networkx",
    ]


def test_live_core_dependency_minimization_audit_passes() -> None:
    assert build_core_dependency_minimization_violations() == ()
    assert run(check=True) == 0


def test_dependency_declarations_reject_required_and_disallowed_optional_heavy_packages() -> (
    None
):
    policy = _policy()
    project_table = {
        "dependencies": ["click>=8.1", "pandas>=2.0"],
        "optional-dependencies": {"analysis": ["pandas>=2.0"]},
    }

    violations = evaluate_dependency_declarations(policy, project_table)

    assert {violation.code for violation in violations} == {
        "forbidden-required-dependency",
        "forbidden-optional-dependency-group",
    }


def test_source_imports_allow_only_declared_optional_prefixes() -> None:
    policy = _policy(
        allowed_optional_module_prefixes=("bijux_proteomics.optional_tables",)
    )
    module_sources = {
        "bijux_proteomics.io.formats": "import pandas as pd\n",
        "bijux_proteomics.optional_tables.writer": "from pandas import DataFrame\n",
    }

    violations = evaluate_source_imports(policy, module_sources)

    assert len(violations) == 1
    assert violations[0].code == "forbidden-import-root"
    assert "bijux_proteomics.io.formats" in violations[0].detail
