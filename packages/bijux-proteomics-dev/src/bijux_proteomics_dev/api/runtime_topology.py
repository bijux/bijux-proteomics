from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "REPO_ROOT",
    "RUNTIME_SRC_ROOT",
    "RUNTIME_TOPOLOGY_PATH",
    "RuntimeSubtreeEntry",
    "RuntimeTopologyBudget",
    "build_runtime_topology_budget",
    "run",
]


@dataclass(frozen=True)
class RuntimeSubtreeEntry:
    """One first-level runtime subtree and its owned Python module count."""

    name: str
    module_count: int


@dataclass(frozen=True)
class RuntimeTopologyBudget:
    """Governed runtime subtree count and the current subtree inventory."""

    max_first_level_subtrees: int
    actual_first_level_subtrees: int
    subtrees: tuple[RuntimeSubtreeEntry, ...]


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for runtime topology")


REPO_ROOT = _repo_root()
RUNTIME_SRC_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-runtime"
    / "src"
    / "bijux_proteomics_runtime"
)
RUNTIME_TOPOLOGY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "runtime-topology.toml"
)


def _subtree_entries() -> tuple[RuntimeSubtreeEntry, ...]:
    entries: list[RuntimeSubtreeEntry] = []
    for path in sorted(
        child
        for child in RUNTIME_SRC_ROOT.iterdir()
        if child.is_dir() and child.name != "__pycache__"
    ):
        module_count = sum(
            1
            for module_path in path.rglob("*.py")
            if "__pycache__" not in module_path.parts
        )
        entries.append(
            RuntimeSubtreeEntry(
                name=path.name,
                module_count=module_count,
            )
        )
    return tuple(entries)


def build_runtime_topology_budget() -> RuntimeTopologyBudget:
    """Build the governed first-level runtime topology budget."""

    subtrees = _subtree_entries()
    return RuntimeTopologyBudget(
        max_first_level_subtrees=len(subtrees),
        actual_first_level_subtrees=len(subtrees),
        subtrees=subtrees,
    )


def _toml_text(budget: RuntimeTopologyBudget) -> str:
    lines = [
        "# Generated runtime topology budget.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.runtime_topology",
        "",
        "[budget]",
        f"max_first_level_subtrees = {budget.max_first_level_subtrees}",
        f"actual_first_level_subtrees = {budget.actual_first_level_subtrees}",
        "",
    ]
    for entry in budget.subtrees:
        lines.extend(
            [
                "[[subtree]]",
                f'name = "{entry.name}"',
                f"module_count = {entry.module_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(budget: RuntimeTopologyBudget) -> bool:
    if not RUNTIME_TOPOLOGY_PATH.exists():
        return False
    return RUNTIME_TOPOLOGY_PATH.read_text(encoding="utf-8") == _toml_text(budget)


def run(check: bool = False) -> int:
    budget = build_runtime_topology_budget()
    if check:
        if _is_up_to_date(budget):
            print(
                "runtime topology budget is up to date for "
                f"{budget.actual_first_level_subtrees} first-level subtrees"
            )
            return 0
        print("runtime topology budget is stale; regenerate it")
        return 1
    RUNTIME_TOPOLOGY_PATH.write_text(_toml_text(budget), encoding="utf-8")
    print(
        "generated runtime topology budget for "
        f"{budget.actual_first_level_subtrees} first-level subtrees"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the governed runtime topology budget."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the runtime topology budget is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
