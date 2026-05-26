from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    module_identifier,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    source_modules,
)

__all__ = [
    "CORE_DEPENDENCY_MINIMIZATION_PATH",
    "CoreDependencyMinimizationPolicy",
    "CoreDependencyMinimizationRule",
    "CoreDependencyMinimizationViolation",
    "build_core_dependency_minimization_violations",
    "evaluate_dependency_declarations",
    "evaluate_source_imports",
    "load_core_dependency_minimization_policy",
    "run",
]


CORE_DEPENDENCY_MINIMIZATION_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "core-dependency-minimization.toml"
)
CORE_DEPENDENCY_MINIMIZATION_ARTIFACTS_DIR = (
    REPO_ROOT / "artifacts" / "root" / "core-dependency-minimization"
)
_DEPENDENCY_NAME_PATTERN = re.compile(r"([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class CoreDependencyMinimizationRule:
    """One governed heavy dependency rule for the core package."""

    distribution_name: str
    forbidden_import_roots: tuple[str, ...]
    allowed_optional_dependency_groups: tuple[str, ...]
    allowed_optional_module_prefixes: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class CoreDependencyMinimizationPolicy:
    """The governed dependency minimization policy for core."""

    package_name: str
    rules: tuple[CoreDependencyMinimizationRule, ...]


@dataclass(frozen=True)
class CoreDependencyMinimizationViolation:
    """One dependency minimization contract failure."""

    package_name: str
    code: str
    detail: str


def _normalize_dependency_name(requirement: str) -> str:
    match = _DEPENDENCY_NAME_PATTERN.match(requirement.strip())
    return match.group(1).lower() if match else requirement.strip().lower()


def load_core_dependency_minimization_policy(
    path: Path = CORE_DEPENDENCY_MINIMIZATION_PATH,
) -> CoreDependencyMinimizationPolicy:
    """Load the governed core dependency minimization policy."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    policy = cast(dict[str, Any], data["policy"])
    entries = cast(list[dict[str, Any]], data["dependency"])
    return CoreDependencyMinimizationPolicy(
        package_name=str(policy["package_name"]),
        rules=tuple(
            CoreDependencyMinimizationRule(
                distribution_name=str(entry["distribution_name"]).lower(),
                forbidden_import_roots=tuple(
                    str(value) for value in entry["forbidden_import_roots"]
                ),
                allowed_optional_dependency_groups=tuple(
                    str(value) for value in entry["allowed_optional_dependency_groups"]
                ),
                allowed_optional_module_prefixes=tuple(
                    str(value) for value in entry["allowed_optional_module_prefixes"]
                ),
                rationale=str(entry["rationale"]),
            )
            for entry in entries
        ),
    )


def evaluate_dependency_declarations(
    policy: CoreDependencyMinimizationPolicy,
    project_table: dict[str, Any],
) -> tuple[CoreDependencyMinimizationViolation, ...]:
    """Evaluate one package pyproject table against the governed policy."""

    violations: list[CoreDependencyMinimizationViolation] = []
    required_dependencies = {
        _normalize_dependency_name(str(value))
        for value in cast(list[str], project_table.get("dependencies", []))
    }
    optional_dependencies = cast(
        dict[str, list[str]],
        project_table.get("optional-dependencies", {}),
    )
    optional_dependency_sets = {
        group_name: {
            _normalize_dependency_name(str(value)) for value in dependency_values
        }
        for group_name, dependency_values in optional_dependencies.items()
    }

    for rule in policy.rules:
        if rule.distribution_name in required_dependencies:
            violations.append(
                CoreDependencyMinimizationViolation(
                    package_name=policy.package_name,
                    code="forbidden-required-dependency",
                    detail=(
                        f"{policy.package_name} declares forbidden required dependency "
                        f"{rule.distribution_name}: {rule.rationale}"
                    ),
                )
            )
        disallowed_optional_groups = sorted(
            group_name
            for group_name, dependencies in optional_dependency_sets.items()
            if rule.distribution_name in dependencies
            and group_name not in rule.allowed_optional_dependency_groups
        )
        if disallowed_optional_groups:
            violations.append(
                CoreDependencyMinimizationViolation(
                    package_name=policy.package_name,
                    code="forbidden-optional-dependency-group",
                    detail=(
                        f"{policy.package_name} exposes {rule.distribution_name} through "
                        f"disallowed optional groups {disallowed_optional_groups}: "
                        f"{rule.rationale}"
                    ),
                )
            )
    return tuple(violations)


def _imported_roots(source_text: str, *, filename: str) -> tuple[str, ...]:
    tree = ast.parse(source_text, filename=filename)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported_roots.add(node.module.split(".")[0])
    return tuple(sorted(imported_roots))


def _module_prefix_match(module_name: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in prefixes
    )


def evaluate_source_imports(
    policy: CoreDependencyMinimizationPolicy,
    module_sources: dict[str, str],
) -> tuple[CoreDependencyMinimizationViolation, ...]:
    """Evaluate source imports against the governed dependency policy."""

    violations: list[CoreDependencyMinimizationViolation] = []
    seen: set[tuple[str, str]] = set()
    for module_name, source_text in sorted(module_sources.items()):
        imported_roots = set(_imported_roots(source_text, filename=module_name))
        for rule in policy.rules:
            forbidden_roots = imported_roots.intersection(rule.forbidden_import_roots)
            if not forbidden_roots:
                continue
            if _module_prefix_match(module_name, rule.allowed_optional_module_prefixes):
                continue
            for forbidden_root in sorted(forbidden_roots):
                key = (module_name, forbidden_root)
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    CoreDependencyMinimizationViolation(
                        package_name=policy.package_name,
                        code="forbidden-import-root",
                        detail=(
                            f"{module_name} imports forbidden root {forbidden_root}: "
                            f"{rule.rationale}"
                        ),
                    )
                )
    return tuple(violations)


def build_core_dependency_minimization_violations(
    policy: CoreDependencyMinimizationPolicy | None = None,
) -> tuple[CoreDependencyMinimizationViolation, ...]:
    """Return live core dependency minimization violations."""

    policy = policy or load_core_dependency_minimization_policy()
    pyproject_path = package_root(policy.package_name) / "pyproject.toml"
    project_table = cast(
        dict[str, Any],
        tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"],
    )
    module_sources = {
        module_identifier(policy.package_name, path): path.read_text(encoding="utf-8")
        for path in source_modules(policy.package_name)
    }
    return tuple(
        sorted(
            (
                *evaluate_dependency_declarations(policy, project_table),
                *evaluate_source_imports(policy, module_sources),
            ),
            key=lambda violation: (violation.code, violation.detail),
        )
    )


def run(*, check: bool = False) -> int:
    """Validate the governed core dependency minimization audit."""

    violations = build_core_dependency_minimization_violations()
    CORE_DEPENDENCY_MINIMIZATION_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = CORE_DEPENDENCY_MINIMIZATION_ARTIFACTS_DIR / "validation.txt"
    if violations:
        artifact_path.write_text(
            "\n".join(violation.detail for violation in violations) + "\n",
            encoding="utf-8",
        )
        for violation in violations:
            print(violation.detail)
        return 1
    artifact_path.write_text(
        "core dependency minimization audit passed\n",
        encoding="utf-8",
    )
    print("core dependency minimization audit passed")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Validate that bijux-proteomics-core stays free of forbidden heavy "
            "dependencies on the default import path."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the governed core dependency minimization audit finds violations.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
