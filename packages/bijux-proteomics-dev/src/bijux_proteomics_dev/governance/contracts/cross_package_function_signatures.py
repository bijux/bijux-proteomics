# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Signature freeze for public functions imported across package boundaries."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import importlib
import inspect
from pathlib import Path
import tomllib

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    module_identifier,
    workspace_import_roots,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    source_modules,
    workspace_import_path,
    workspace_package_names,
)

__all__ = [
    "CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH",
    "CrossPackageFunctionImportSite",
    "CrossPackageFunctionSignatureEntry",
    "CrossPackageFunctionSignatureReport",
    "build_cross_package_function_signature_report",
    "find_cross_package_function_signature_entry",
    "run",
    "validate_cross_package_function_signatures",
]


CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "cross-package-function-signatures.toml"
)

_COMPATIBILITY_ALIAS_DISTRIBUTIONS = {
    "bijux-proteomics",
    "proteomics",
    "proteomics-core",
    "proteomics-foundation",
    "proteomics-runtime",
    "proteomics-intelligence",
    "proteomics-knowledge",
    "proteomics-lab",
}


@dataclass(frozen=True)
class CrossPackageFunctionImportSite:
    """One consumer module importing a public function from another package."""

    consumer_distribution: str
    consumer_module: str


@dataclass(frozen=True)
class CrossPackageFunctionSignatureEntry:
    """One public cross-package function with its frozen signature text."""

    provider_distribution: str
    provider_module: str
    function_name: str
    signature_text: str
    import_sites: tuple[CrossPackageFunctionImportSite, ...]

    @property
    def consumer_distributions(self) -> tuple[str, ...]:
        return tuple(
            sorted({site.consumer_distribution for site in self.import_sites})
        )

    @property
    def consumer_modules(self) -> tuple[str, ...]:
        return tuple(site.consumer_module for site in self.import_sites)

    @property
    def symbol_path(self) -> str:
        return f"{self.provider_module}.{self.function_name}"


@dataclass(frozen=True)
class CrossPackageFunctionSignatureReport:
    """Generated signature ledger for public functions imported across packages."""

    entries: tuple[CrossPackageFunctionSignatureEntry, ...]


def _tracked_workspace_packages() -> tuple[str, ...]:
    return tuple(
        package_name
        for package_name in workspace_package_names()
        if package_name not in _COMPATIBILITY_ALIAS_DISTRIBUTIONS
    )


def _module_is_public(module_name: str) -> bool:
    return not any(part.startswith("_") for part in module_name.split(".")[1:])


def _import_references() -> dict[
    tuple[str, str, str],
    set[tuple[str, str]],
]:
    roots = workspace_import_roots()
    references: dict[tuple[str, str, str], set[tuple[str, str]]] = {}
    tracked_packages = set(_tracked_workspace_packages())
    for consumer_distribution in _tracked_workspace_packages():
        for path in source_modules(consumer_distribution):
            source_module = module_identifier(consumer_distribution, path)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.level != 0 or node.module is None:
                    continue
                provider_root = node.module.split(".")[0]
                provider_distribution = roots.get(provider_root)
                if (
                    provider_distribution is None
                    or provider_distribution == consumer_distribution
                    or provider_distribution not in tracked_packages
                    or not _module_is_public(node.module)
                ):
                    continue
                for alias in node.names:
                    if alias.name == "*" or alias.name.startswith("_"):
                        continue
                    references.setdefault(
                        (provider_distribution, node.module, alias.name),
                        set(),
                    ).add((consumer_distribution, source_module))
    return references


def build_cross_package_function_signature_report() -> CrossPackageFunctionSignatureReport:
    """Build the live report of imported public cross-package function signatures."""

    entries: list[CrossPackageFunctionSignatureEntry] = []
    with workspace_import_path():
        for (
            provider_distribution,
            provider_module,
            function_name,
        ), import_sites in sorted(_import_references().items()):
            module = importlib.import_module(provider_module)
            function = getattr(module, function_name)
            if not (inspect.isfunction(function) or inspect.isbuiltin(function)):
                continue
            entries.append(
                CrossPackageFunctionSignatureEntry(
                    provider_distribution=provider_distribution,
                    provider_module=provider_module,
                    function_name=function_name,
                    signature_text=str(inspect.signature(function)),
                    import_sites=tuple(
                        CrossPackageFunctionImportSite(
                            consumer_distribution=consumer_distribution,
                            consumer_module=consumer_module,
                        )
                        for consumer_distribution, consumer_module in sorted(import_sites)
                    ),
                )
            )
    return CrossPackageFunctionSignatureReport(entries=tuple(entries))


def find_cross_package_function_signature_entry(
    report: CrossPackageFunctionSignatureReport,
    *,
    provider_module: str,
    function_name: str,
) -> CrossPackageFunctionSignatureEntry:
    """Return one signature entry by stable provider symbol path."""

    for entry in report.entries:
        if (
            entry.provider_module == provider_module
            and entry.function_name == function_name
        ):
            return entry
    raise KeyError(f"unknown cross-package function signature entry {provider_module}.{function_name}")


def _entry_key(entry: CrossPackageFunctionSignatureEntry) -> tuple[str, str]:
    return (entry.provider_module, entry.function_name)


def _load_report(path: Path = CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH) -> CrossPackageFunctionSignatureReport:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    entries: list[CrossPackageFunctionSignatureEntry] = []
    for item in data.get("entry", []):
        entries.append(
            CrossPackageFunctionSignatureEntry(
                provider_distribution=item["provider_distribution"],
                provider_module=item["provider_module"],
                function_name=item["function_name"],
                signature_text=item["signature_text"],
                import_sites=tuple(
                    CrossPackageFunctionImportSite(
                        consumer_distribution=site["consumer_distribution"],
                        consumer_module=site["consumer_module"],
                    )
                    for site in item["import_site"]
                ),
            )
        )
    return CrossPackageFunctionSignatureReport(entries=tuple(entries))


def validate_cross_package_function_signatures(
    report: CrossPackageFunctionSignatureReport | None = None,
    *,
    baseline_path: Path = CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH,
) -> tuple[str, ...]:
    """Detect missing, added, or drifted public cross-package function signatures."""

    report = report or build_cross_package_function_signature_report()
    if not baseline_path.exists():
        return (f"missing baseline report {baseline_path}",)
    baseline = _load_report(baseline_path)
    live_by_key = {_entry_key(entry): entry for entry in report.entries}
    baseline_by_key = {_entry_key(entry): entry for entry in baseline.entries}
    failures: list[str] = []

    missing = sorted(set(baseline_by_key) - set(live_by_key))
    added = sorted(set(live_by_key) - set(baseline_by_key))
    for provider_module, function_name in missing:
        failures.append(
            f"missing shared function snapshot {provider_module}.{function_name}"
        )
    for provider_module, function_name in added:
        failures.append(
            f"new shared function snapshot {provider_module}.{function_name} requires baseline refresh"
        )
    for key in sorted(set(live_by_key) & set(baseline_by_key)):
        live_entry = live_by_key[key]
        baseline_entry = baseline_by_key[key]
        if live_entry.signature_text != baseline_entry.signature_text:
            failures.append(
                f"signature drift for {live_entry.symbol_path}: "
                f"{baseline_entry.signature_text} -> {live_entry.signature_text}"
            )
        if live_entry.consumer_distributions != baseline_entry.consumer_distributions:
            failures.append(
                f"consumer distribution drift for {live_entry.symbol_path}: "
                f"{baseline_entry.consumer_distributions} -> {live_entry.consumer_distributions}"
            )
        if live_entry.consumer_modules != baseline_entry.consumer_modules:
            failures.append(
                f"consumer module drift for {live_entry.symbol_path}"
            )
    return tuple(failures)


def _toml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_text(report: CrossPackageFunctionSignatureReport) -> str:
    lines = [
        "# Generated cross-package function signature freeze report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.contracts.cross_package_function_signatures",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[entry]]",
                f"provider_distribution = {_toml_quote(entry.provider_distribution)}",
                f"provider_module = {_toml_quote(entry.provider_module)}",
                f"function_name = {_toml_quote(entry.function_name)}",
                f"signature_text = {_toml_quote(entry.signature_text)}",
                "consumer_distributions = ["
                + ", ".join(_toml_quote(value) for value in entry.consumer_distributions)
                + "]",
                "consumer_modules = ["
                + ", ".join(_toml_quote(value) for value in entry.consumer_modules)
                + "]",
            ]
        )
        for site in entry.import_sites:
            lines.extend(
                [
                    "[[entry.import_site]]",
                    f"consumer_distribution = {_toml_quote(site.consumer_distribution)}",
                    f"consumer_module = {_toml_quote(site.consumer_module)}",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def _is_up_to_date(report: CrossPackageFunctionSignatureReport) -> bool:
    if not CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH.exists():
        return False
    return CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_cross_package_function_signature_report()
    if check:
        failures = validate_cross_package_function_signatures(report)
        if failures:
            for failure in failures:
                print(failure)
            return 1
        if _is_up_to_date(report):
            print("cross-package function signature report is up to date")
            return 0
        print("cross-package function signature report is stale; regenerate it")
        return 1
    CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH.write_text(
        _toml_text(report),
        encoding="utf-8",
    )
    print("generated cross-package function signature report")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or validate the cross-package function signature freeze report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the cross-package function signature report is not up to date.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
