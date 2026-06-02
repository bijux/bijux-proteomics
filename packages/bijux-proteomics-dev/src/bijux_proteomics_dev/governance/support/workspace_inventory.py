from __future__ import annotations

import ast
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import sys
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

WORKSPACE_IMPORT_ROOTS = (
    "agentic_proteins",
    "bijux_proteomics_alias",
    "bijux_proteomics",
    "bijux_proteomics_dev",
    "bijux_proteomics_foundation",
    "bijux_proteomics_intelligence",
    "bijux_proteomics_knowledge",
    "bijux_proteomics_lab",
    "bijux_proteomics_runtime",
    "proteomics",
    "proteomics_core",
    "proteomics_foundation",
    "proteomics_intelligence",
    "proteomics_knowledge",
    "proteomics_lab",
    "proteomics_runtime",
)
ROOT_API_POLICY_DIR = REPO_ROOT / "configs" / "package-governance"


@lru_cache(maxsize=1)
def workspace_package_names() -> tuple[str, ...]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    workspace = cast(dict[str, Any], data["tool"]["bijux_proteomics"])
    return tuple(cast(list[str], workspace["packages"]))


def import_root(package_name: str) -> str:
    if package_name == "bijux-proteomics-core":
        return "bijux_proteomics"
    if package_name == "bijux-proteomics":
        return "bijux_proteomics_alias"
    return package_name.replace("-", "_")


def package_root(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def src_root(package_name: str) -> Path:
    return package_root(package_name) / "src" / import_root(package_name)


def workspace_src_parents() -> tuple[Path, ...]:
    return tuple(
        src_root(package_name).parent for package_name in workspace_package_names()
    )


@contextmanager
def workspace_import_path() -> Iterator[None]:
    additions = [
        str(path)
        for path in reversed(workspace_src_parents())
        if str(path) not in sys.path
    ]
    for path in reversed(additions):
        sys.path.insert(0, path)
    try:
        yield
    finally:
        for path in additions:
            if path in sys.path:
                sys.path.remove(path)


def tests_root(package_name: str) -> Path:
    return package_root(package_name) / "tests"


def docs_root(package_name: str) -> Path | None:
    path = package_root(package_name) / "docs"
    return path if path.exists() else None


def fixture_root(package_name: str) -> Path | None:
    path = tests_root(package_name) / "fixtures"
    return path if path.exists() else None


def source_modules(package_name: str) -> tuple[Path, ...]:
    return tuple(sorted(src_root(package_name).rglob("*.py")))


def root_python_modules(package_name: str) -> tuple[Path, ...]:
    return tuple(sorted(src_root(package_name).glob("*.py")))


def source_owner_families(package_name: str) -> tuple[str, ...]:
    root = src_root(package_name)
    return tuple(
        sorted(
            path.name
            for path in root.iterdir()
            if path.is_dir() and path.name != "__pycache__"
        )
    )


def test_families(package_name: str) -> tuple[str, ...]:
    root = tests_root(package_name)
    if not root.exists():
        return ()
    return tuple(
        sorted(
            path.name
            for path in root.iterdir()
            if path.is_dir() and path.name not in {"__pycache__", "fixtures"}
        )
    )


def flat_test_modules(package_name: str) -> tuple[Path, ...]:
    root = tests_root(package_name)
    if not root.exists():
        return ()
    return tuple(sorted(root.glob("test_*.py")))


def package_test_modules(package_name: str) -> tuple[Path, ...]:
    root = tests_root(package_name)
    if not root.exists():
        return ()
    return tuple(sorted(root.rglob("test_*.py")))


def fixture_files(package_name: str) -> tuple[Path, ...]:
    root = fixture_root(package_name)
    if root is None:
        return ()
    return tuple(sorted(path for path in root.rglob("*") if path.is_file()))


def package_docs(package_name: str) -> tuple[Path, ...]:
    docs: list[Path] = []
    readme_path = package_root(package_name) / "README.md"
    if readme_path.exists():
        docs.append(readme_path)
    package_docs_root = docs_root(package_name)
    if package_docs_root is not None:
        docs.extend(sorted(package_docs_root.glob("*.md")))
    return tuple(docs)


def nonempty_line_count(path: Path) -> int:
    return sum(
        1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    )


def public_symbol_count_from_init(package_name: str) -> int:
    init_path = src_root(package_name) / "__init__.py"
    if not init_path.exists():
        return 0
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "__all__"
                and isinstance(node.value, (ast.List, ast.Tuple))
            ):
                return len(node.value.elts)
    return 0


def public_definition_counts(path: Path) -> tuple[int, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    public_functions = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
        for node in tree.body
    )
    public_classes = sum(
        isinstance(node, ast.ClassDef) and not node.name.startswith("_")
        for node in tree.body
    )
    return public_functions, public_classes


def workspace_import_roots_used(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for root_name in WORKSPACE_IMPORT_ROOTS:
                    if alias.name == root_name or alias.name.startswith(
                        f"{root_name}."
                    ):
                        used.add(root_name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for root_name in WORKSPACE_IMPORT_ROOTS:
                if node.module == root_name or node.module.startswith(f"{root_name}."):
                    used.add(root_name)
    return tuple(sorted(used))


def package_root_import_occurrences(
    package_name: str,
) -> tuple[tuple[str, str, int], ...]:
    root_name = import_root(package_name)
    occurrences: list[tuple[str, str, int]] = []
    for path in source_modules(package_name):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(src_root(package_name)).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == root_name:
                        occurrences.append((relative, "import", node.lineno))
            elif isinstance(node, ast.ImportFrom) and node.module == root_name:
                occurrences.append((relative, "from", node.lineno))
    return tuple(sorted(occurrences))


def is_wrapper_module(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    public_functions, public_classes = public_definition_counts(path)
    if public_functions or public_classes:
        return False
    allowed_nodes = (
        ast.Assign,
        ast.Expr,
        ast.Import,
        ast.ImportFrom,
        ast.Pass,
        ast.AnnAssign,
    )
    return all(isinstance(node, allowed_nodes) for node in tree.body)


def root_api_policy_path(package_name: str) -> Path | None:
    stem = package_name.removeprefix("bijux-proteomics-")
    if package_name == "agentic-proteins":
        return None
    path = ROOT_API_POLICY_DIR / f"{stem}-root-api.toml"
    return path if path.exists() else None


def root_api_policy_budget(package_name: str) -> dict[str, int] | None:
    path = root_api_policy_path(package_name)
    if path is None:
        return None
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, int], data["budget"])
