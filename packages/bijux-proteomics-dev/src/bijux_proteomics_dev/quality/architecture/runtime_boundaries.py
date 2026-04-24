from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any

from bijux_proteomics_dev.quality.architecture.scanner import (
    import_references,
    iter_python_files,
    parse_python_module,
    top_level_class_names,
)


@dataclass(frozen=True)
class RuntimeImportPolicy:
    runtime_import_prefix: str
    lower_layer_roots: tuple[Path, ...]


@dataclass(frozen=True)
class CompatForwardingPolicy:
    package_root: Path
    forwarding_target_prefixes: tuple[str, ...]
    non_forwarding_allowlist_path: Path


@dataclass(frozen=True)
class RuntimeTypeOwnershipPolicy:
    runtime_root: Path
    canonical_roots: tuple[Path, ...]
    runtime_type_overlap_allowlist_path: Path


@dataclass(frozen=True)
class RuntimeBoundaryPolicy:
    runtime_imports: RuntimeImportPolicy
    compat_forwarding: CompatForwardingPolicy
    runtime_type_ownership: RuntimeTypeOwnershipPolicy


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_policy(repo_root: Path) -> RuntimeBoundaryPolicy:
    raw = _load_toml(repo_root / "configs" / "runtime-boundaries" / "policy.toml")
    imports = raw["imports"]
    compat = raw["compat"]
    compat_prefixes_raw = compat.get("forwarding_target_prefixes")
    compat_prefixes: tuple[str, ...]
    if compat_prefixes_raw is not None:
        compat_prefixes = tuple(str(item) for item in compat_prefixes_raw)
    else:
        compat_prefixes = (str(compat["forwarding_target_prefix"]),)
    ownership = raw["runtime_type_ownership"]
    return RuntimeBoundaryPolicy(
        runtime_imports=RuntimeImportPolicy(
            runtime_import_prefix=str(imports["runtime_import_prefix"]),
            lower_layer_roots=tuple(
                repo_root / str(item) for item in imports["lower_layer_roots"]
            ),
        ),
        compat_forwarding=CompatForwardingPolicy(
            package_root=repo_root / str(compat["package_root"]),
            forwarding_target_prefixes=compat_prefixes,
            non_forwarding_allowlist_path=repo_root
            / str(compat["non_forwarding_allowlist_path"]),
        ),
        runtime_type_ownership=RuntimeTypeOwnershipPolicy(
            runtime_root=repo_root / str(ownership["runtime_root"]),
            canonical_roots=tuple(
                repo_root / str(item) for item in ownership["canonical_roots"]
            ),
            runtime_type_overlap_allowlist_path=repo_root
            / str(ownership["runtime_type_overlap_allowlist_path"]),
        ),
    )


def _allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    values: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        values.add(value)
    return values


def _is_forwarding_module(tree: ast.Module, target_prefixes: tuple[str, ...]) -> bool:
    def _matches_target(module_name: str) -> bool:
        return any(
            module_name == target_prefix or module_name.startswith(f"{target_prefix}.")
            for target_prefix in target_prefixes
        )

    module_aliases: set[str] = set()
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                continue
            if (
                all(isinstance(target, ast.Name) for target in node.targets)
                and isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id in module_aliases
            ):
                continue
            return False
        if isinstance(node, ast.Import):
            if all(_matches_target(alias.name) for alias in node.names):
                for alias in node.names:
                    if alias.asname:
                        module_aliases.add(alias.asname)
                continue
            return False
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _matches_target(module):
                for alias in node.names:
                    if alias.asname:
                        module_aliases.add(alias.asname)
                continue
            return False
        return False
    return True


def check_agentic_compat_forwarding(policy: RuntimeBoundaryPolicy) -> list[str]:
    failures: list[str] = []
    allowlist = _allowlist(policy.compat_forwarding.non_forwarding_allowlist_path)

    for path in iter_python_files(policy.compat_forwarding.package_root):
        if path.name == "__init__.py":
            continue
        relative_path = path.relative_to(
            policy.compat_forwarding.package_root
        ).as_posix()
        tree = parse_python_module(path).tree
        if _is_forwarding_module(
            tree, policy.compat_forwarding.forwarding_target_prefixes
        ):
            continue
        if relative_path not in allowlist:
            failures.append(
                f"{path}: compat package module is not forwarding-only ({relative_path})"
            )

    return failures


def _class_index(root: Path) -> dict[str, list[str]]:
    classes: dict[str, list[str]] = {}
    for path in iter_python_files(root):
        tree = parse_python_module(path).tree
        for class_name in top_level_class_names(tree):
            classes.setdefault(class_name, []).append(str(path))
    return classes


def check_runtime_type_collisions(policy: RuntimeBoundaryPolicy) -> list[str]:
    failures: list[str] = []
    allowlist = _allowlist(
        policy.runtime_type_ownership.runtime_type_overlap_allowlist_path
    )
    runtime_classes = _class_index(policy.runtime_type_ownership.runtime_root)

    canonical_classes: dict[str, list[str]] = {}
    for root in policy.runtime_type_ownership.canonical_roots:
        for class_name, paths in _class_index(root).items():
            canonical_classes.setdefault(class_name, []).extend(paths)

    for class_name, runtime_paths in sorted(runtime_classes.items()):
        if class_name in allowlist:
            continue
        if class_name not in canonical_classes:
            continue
        for runtime_path in runtime_paths:
            canonical_sources = ", ".join(sorted(canonical_classes[class_name]))
            failures.append(
                "runtime type collision: "
                f"class '{class_name}' in {runtime_path} duplicates canonical owner "
                f"types from {canonical_sources}"
            )

    return failures


def check_lower_layer_runtime_imports(policy: RuntimeBoundaryPolicy) -> list[str]:
    failures: list[str] = []
    runtime_prefix = policy.runtime_imports.runtime_import_prefix

    for root in policy.runtime_imports.lower_layer_roots:
        for path in iter_python_files(root):
            module = parse_python_module(path)
            imports = import_references(module.tree)
            for imported in imports:
                if imported == runtime_prefix or imported.startswith(
                    f"{runtime_prefix}."
                ):
                    failures.append(
                        f"{path}: lower-layer package imports runtime module '{imported}'"
                    )

    return failures


def check_runtime_imports_compat_package(policy: RuntimeBoundaryPolicy) -> list[str]:
    failures: list[str] = []
    compat_import_prefix = "agentic_proteins"

    for path in iter_python_files(policy.runtime_type_ownership.runtime_root):
        module = parse_python_module(path)
        for imported in import_references(module.tree):
            if imported == compat_import_prefix or imported.startswith(
                f"{compat_import_prefix}."
            ):
                failures.append(
                    f"{path}: runtime package imports compat module '{imported}'"
                )

    return failures


def run(repo_root: Path) -> int:
    policy = load_policy(repo_root)
    failures = [
        *check_lower_layer_runtime_imports(policy),
        *check_runtime_imports_compat_package(policy),
        *check_agentic_compat_forwarding(policy),
        *check_runtime_type_collisions(policy),
    ]

    if failures:
        print("runtime-boundary-check failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("runtime-boundary-check passed")
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
