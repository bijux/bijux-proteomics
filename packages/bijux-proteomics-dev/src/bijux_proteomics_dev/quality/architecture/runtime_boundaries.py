from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import tomllib
from typing import Any

from bijux_proteomics_dev.quality.architecture.scanner import (
    import_references,
    iter_python_files,
    parse_python_module,
)


@dataclass(frozen=True)
class RuntimeImportPolicy:
    runtime_import_prefix: str
    lower_layer_roots: tuple[Path, ...]


@dataclass(frozen=True)
class CompatForwardingPolicy:
    package_root: Path
    forwarding_target_prefix: str
    non_forwarding_allowlist_path: Path


@dataclass(frozen=True)
class RuntimeBoundaryPolicy:
    runtime_imports: RuntimeImportPolicy
    compat_forwarding: CompatForwardingPolicy


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_policy(repo_root: Path) -> RuntimeBoundaryPolicy:
    raw = _load_toml(repo_root / "configs" / "runtime-boundaries" / "policy.toml")
    imports = raw["imports"]
    compat = raw["compat"]
    return RuntimeBoundaryPolicy(
        runtime_imports=RuntimeImportPolicy(
            runtime_import_prefix=str(imports["runtime_import_prefix"]),
            lower_layer_roots=tuple(
                repo_root / str(item) for item in imports["lower_layer_roots"]
            ),
        ),
        compat_forwarding=CompatForwardingPolicy(
            package_root=repo_root / str(compat["package_root"]),
            forwarding_target_prefix=str(compat["forwarding_target_prefix"]),
            non_forwarding_allowlist_path=repo_root
            / str(compat["non_forwarding_allowlist_path"]),
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


def _is_forwarding_module(tree: ast.Module, target_prefix: str) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                continue
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                continue
            return False
        if isinstance(node, ast.Import):
            imported = [alias.name for alias in node.names]
            if all(
                name == target_prefix or name.startswith(f"{target_prefix}.")
                for name in imported
            ):
                continue
            return False
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == target_prefix or module.startswith(f"{target_prefix}."):
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
        relative_path = path.relative_to(policy.compat_forwarding.package_root).as_posix()
        tree = parse_python_module(path).tree
        if _is_forwarding_module(tree, policy.compat_forwarding.forwarding_target_prefix):
            continue
        if relative_path not in allowlist:
            failures.append(
                f"{path}: compat package module is not forwarding-only ({relative_path})"
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


def run(repo_root: Path) -> int:
    policy = load_policy(repo_root)
    failures = check_lower_layer_runtime_imports(policy)

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
