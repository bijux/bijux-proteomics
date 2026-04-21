from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
class RuntimeBoundaryPolicy:
    runtime_imports: RuntimeImportPolicy


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_policy(repo_root: Path) -> RuntimeBoundaryPolicy:
    raw = _load_toml(repo_root / "configs" / "runtime-boundaries" / "policy.toml")
    imports = raw["imports"]
    return RuntimeBoundaryPolicy(
        runtime_imports=RuntimeImportPolicy(
            runtime_import_prefix=str(imports["runtime_import_prefix"]),
            lower_layer_roots=tuple(
                repo_root / str(item) for item in imports["lower_layer_roots"]
            ),
        )
    )


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
