from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import importlib
from pathlib import Path

__all__ = [
    "FOUNDATION_ROOT_CONSUMERS_PATH",
    "FoundationRootConsumerEntry",
    "build_foundation_root_consumers",
    "run",
    "validate_foundation_root_consumers",
]


@dataclass(frozen=True)
class DownstreamPackage:
    """One downstream package that may import foundation root symbols."""

    distribution_name: str
    import_root: str


@dataclass(frozen=True)
class FoundationRootConsumerEntry:
    """One curated foundation root export and its downstream consumers."""

    symbol_name: str
    consumer_distributions: tuple[str, ...]
    consumer_modules: tuple[str, ...]


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for foundation consumers")


REPO_ROOT = _repo_root()
FOUNDATION_ROOT_CONSUMERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-root-consumers.toml"
)


def downstream_packages() -> tuple[DownstreamPackage, ...]:
    """Return downstream source roots that may consume foundation exports."""

    return (
        DownstreamPackage("agentic-proteins", "agentic_proteins"),
        DownstreamPackage("bijux-proteomics-core", "bijux_proteomics"),
        DownstreamPackage("bijux-proteomics-dev", "bijux_proteomics_dev"),
        DownstreamPackage("bijux-proteomics-intelligence", "bijux_proteomics_intelligence"),
        DownstreamPackage("bijux-proteomics-knowledge", "bijux_proteomics_knowledge"),
        DownstreamPackage("bijux-proteomics-lab", "bijux_proteomics_lab"),
        DownstreamPackage("bijux-proteomics-runtime", "bijux_proteomics_runtime"),
    )


def _foundation_root_exports() -> tuple[str, ...]:
    module = importlib.import_module("bijux_proteomics_foundation")
    return tuple(getattr(module, "__all__", ()))


def _src_root(package: DownstreamPackage) -> Path:
    return REPO_ROOT / "packages" / package.distribution_name / "src" / package.import_root


def build_foundation_root_consumers() -> tuple[FoundationRootConsumerEntry, ...]:
    """Build the machine-readable consumer matrix for foundation root exports."""

    exports = _foundation_root_exports()
    consumers_by_symbol: dict[str, set[str]] = {symbol_name: set() for symbol_name in exports}
    distributions_by_symbol: dict[str, set[str]] = {
        symbol_name: set() for symbol_name in exports
    }

    for package in downstream_packages():
        src_root = _src_root(package)
        if not src_root.exists():
            continue
        for path in src_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module != "bijux_proteomics_foundation":
                    continue
                for alias in node.names:
                    symbol_name = alias.name
                    if symbol_name not in consumers_by_symbol:
                        continue
                    distributions_by_symbol[symbol_name].add(package.distribution_name)
                    consumers_by_symbol[symbol_name].add(
                        path.relative_to(REPO_ROOT).as_posix()
                    )

    return tuple(
        FoundationRootConsumerEntry(
            symbol_name=symbol_name,
            consumer_distributions=tuple(sorted(distributions_by_symbol[symbol_name])),
            consumer_modules=tuple(sorted(consumers_by_symbol[symbol_name])),
        )
        for symbol_name in exports
    )


def validate_foundation_root_consumers() -> tuple[str, ...]:
    """Validate that every curated root export has at least one downstream consumer."""

    failures: list[str] = []
    for entry in build_foundation_root_consumers():
        if entry.consumer_modules:
            continue
        failures.append(
            f"foundation root export {entry.symbol_name!r} has no downstream src consumers"
        )
    return tuple(failures)


def _toml_text(entries: tuple[FoundationRootConsumerEntry, ...]) -> str:
    lines = [
        "# Generated foundation root consumer matrix.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation_root_consumers",
        "",
    ]
    for entry in entries:
        distributions = ", ".join(f'"{value}"' for value in entry.consumer_distributions)
        modules = ", ".join(f'"{value}"' for value in entry.consumer_modules)
        lines.extend(
            [
                "[[symbol]]",
                f'name = "{entry.symbol_name}"',
                f"consumer_count = {len(entry.consumer_modules)}",
                f"consumer_distributions = [{distributions}]",
                f"consumer_modules = [{modules}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[FoundationRootConsumerEntry, ...]) -> bool:
    if not FOUNDATION_ROOT_CONSUMERS_PATH.exists():
        return False
    return FOUNDATION_ROOT_CONSUMERS_PATH.read_text(encoding="utf-8") == _toml_text(
        entries
    )


def run(check: bool = False) -> int:
    entries = build_foundation_root_consumers()
    failures = validate_foundation_root_consumers()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(entries):
            print(
                f"foundation root consumer matrix is up to date for {len(entries)} symbols"
            )
            return 0
        print("foundation root consumer matrix is stale; regenerate it")
        return 1
    FOUNDATION_ROOT_CONSUMERS_PATH.write_text(_toml_text(entries), encoding="utf-8")
    print(f"generated foundation root consumer matrix for {len(entries)} symbols")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation root consumer matrix."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the consumer matrix is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
