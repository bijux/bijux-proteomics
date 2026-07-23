from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.docs.governance.package_document_contracts import (
    module_topology_tokens,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    root_python_modules,
    source_owner_families,
    src_root,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_TOPOLOGY_DRIFT_PATH",
    "PackageTopologyDriftEntry",
    "PackageTopologyDriftGuard",
    "PackageTopologyDriftReport",
    "build_package_topology_drift_report",
    "run",
    "validate_package_topology_drift",
]


PACKAGE_TOPOLOGY_DRIFT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-topology-drift.toml"
)


@dataclass(frozen=True)
class PackageTopologyDriftEntry:
    """One package's current topology drift between docs and tree."""

    distribution_name: str
    top_level_root_file_count: int
    documented_owner_families: tuple[str, ...]
    undocumented_owner_families: tuple[str, ...]
    stale_documented_paths: tuple[str, ...]
    historical_topology_mentions: tuple[str, ...]
    docs_tree_contradiction: bool
    historical_shape_dominates_design: bool


@dataclass(frozen=True)
class PackageTopologyDriftGuard:
    """Release-blocking baseline for topology drift."""

    max_total_top_level_root_file_count: int
    max_total_undocumented_owner_family_count: int
    max_total_stale_documented_path_count: int
    max_total_historical_shape_count: int


@dataclass(frozen=True)
class PackageTopologyDriftReport:
    """Checked topology drift report across workspace packages."""

    entries: tuple[PackageTopologyDriftEntry, ...]
    guard: PackageTopologyDriftGuard


def _documented_owner_families(package_name: str) -> tuple[str, ...]:
    values: set[str] = set()
    for token in module_topology_tokens(package_name):
        candidate = token.rstrip("/")
        root_name = import_root(package_name)
        if candidate.startswith(f"{root_name}/"):
            candidate = candidate[len(root_name) + 1 :]
        elif candidate.startswith(f"{root_name}."):
            candidate = candidate[len(root_name) + 1 :].replace(".", "/")
        if "/" in candidate:
            values.add(candidate.split("/", 1)[0])
        elif token.endswith("/"):
            values.add(candidate)
    return tuple(sorted(values))


def _path_exists_in_src(package_name: str, token: str) -> bool:
    root = src_root(package_name)
    root_name = import_root(package_name)
    candidate = token
    if candidate.startswith(f"{root_name}/"):
        candidate = candidate[len(root_name) + 1 :]
    if candidate.startswith(f"{root_name}."):
        candidate = candidate[len(root_name) + 1 :].replace(".", "/")
    candidate_path = root / candidate
    if candidate_path.exists():
        return True
    if not candidate_path.suffix and (candidate_path / "__init__.py").exists():
        return True
    return candidate_path.suffix == ".py" and candidate_path.exists()


def _historical_topology_mentions(
    package_name: str, stale_documented_paths: tuple[str, ...]
) -> tuple[str, ...]:
    root_files = {path.name for path in root_python_modules(package_name)}
    mentions: set[str] = set()
    for token in stale_documented_paths:
        if token.endswith(".py") or "/" not in token:
            mentions.add(token)
    for token in module_topology_tokens(package_name):
        if token in root_files and token not in {"__init__.py", "charter.py"}:
            mentions.add(token)
    return tuple(sorted(mentions))


def build_package_topology_drift_report() -> PackageTopologyDriftReport:
    """Build the checked package topology drift report."""

    entries: list[PackageTopologyDriftEntry] = []
    for package_name in workspace_package_names():
        owners = source_owner_families(package_name)
        documented = _documented_owner_families(package_name)
        undocumented = tuple(sorted(set(owners) - set(documented)))
        stale_paths = tuple(
            sorted(
                token
                for token in module_topology_tokens(package_name)
                if not _path_exists_in_src(package_name, token.rstrip("/"))
            )
        )
        historical_mentions = _historical_topology_mentions(package_name, stale_paths)
        top_level_root_file_count = sum(
            path.name not in {"__init__.py", "charter.py"}
            for path in root_python_modules(package_name)
        )
        docs_tree_contradiction = bool(undocumented or stale_paths)
        historical_shape_dominates_design = len(historical_mentions) >= max(
            len(documented), 1
        )
        entries.append(
            PackageTopologyDriftEntry(
                distribution_name=package_name,
                top_level_root_file_count=top_level_root_file_count,
                documented_owner_families=documented,
                undocumented_owner_families=undocumented,
                stale_documented_paths=stale_paths,
                historical_topology_mentions=historical_mentions,
                docs_tree_contradiction=docs_tree_contradiction,
                historical_shape_dominates_design=historical_shape_dominates_design,
            )
        )
    return PackageTopologyDriftReport(
        entries=tuple(entries),
        guard=PackageTopologyDriftGuard(
            max_total_top_level_root_file_count=sum(
                entry.top_level_root_file_count for entry in entries
            ),
            max_total_undocumented_owner_family_count=sum(
                len(entry.undocumented_owner_families) for entry in entries
            ),
            max_total_stale_documented_path_count=sum(
                len(entry.stale_documented_paths) for entry in entries
            ),
            max_total_historical_shape_count=sum(
                entry.historical_shape_dominates_design for entry in entries
            ),
        ),
    )


def validate_package_topology_drift(
    report: PackageTopologyDriftReport | None = None,
) -> tuple[str, ...]:
    """Fail release when topology docs drift or new topology debt appears."""

    report = report or build_package_topology_drift_report()
    failures: list[str] = []
    contradictions = tuple(
        entry.distribution_name
        for entry in report.entries
        if entry.docs_tree_contradiction
    )
    if contradictions:
        failures.append(
            "docs and tree still contradict each other in " + ", ".join(contradictions)
        )
    total_top_level_root_file_count = sum(
        entry.top_level_root_file_count for entry in report.entries
    )
    total_undocumented_owner_family_count = sum(
        len(entry.undocumented_owner_families) for entry in report.entries
    )
    total_stale_documented_path_count = sum(
        len(entry.stale_documented_paths) for entry in report.entries
    )
    total_historical_shape_count = sum(
        entry.historical_shape_dominates_design for entry in report.entries
    )
    if (
        total_top_level_root_file_count
        > report.guard.max_total_top_level_root_file_count
    ):
        failures.append(
            "top-level root file pressure grew beyond the governed topology baseline"
        )
    if (
        total_undocumented_owner_family_count
        > report.guard.max_total_undocumented_owner_family_count
    ):
        failures.append(
            "first-level owner families without written topology rationale grew beyond the governed baseline"
        )
    if (
        total_stale_documented_path_count
        > report.guard.max_total_stale_documented_path_count
    ):
        failures.append(
            "docs-versus-tree contradiction count grew beyond the governed topology baseline"
        )
    if total_historical_shape_count > report.guard.max_total_historical_shape_count:
        failures.append(
            "historical topology pressure grew beyond the governed baseline"
        )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageTopologyDriftReport) -> str:
    lines = [
        "# Generated package topology drift report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_topology_drift",
        "",
        "[guard]",
        f"max_total_top_level_root_file_count = {report.guard.max_total_top_level_root_file_count}",
        (
            "max_total_undocumented_owner_family_count = "
            f"{report.guard.max_total_undocumented_owner_family_count}"
        ),
        (
            "max_total_stale_documented_path_count = "
            f"{report.guard.max_total_stale_documented_path_count}"
        ),
        f"max_total_historical_shape_count = {report.guard.max_total_historical_shape_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"top_level_root_file_count = {entry.top_level_root_file_count}",
                f"documented_owner_families = [{_render_tuple(entry.documented_owner_families)}]",
                f"undocumented_owner_families = [{_render_tuple(entry.undocumented_owner_families)}]",
                f"stale_documented_paths = [{_render_tuple(entry.stale_documented_paths)}]",
                (
                    "historical_topology_mentions = "
                    f"[{_render_tuple(entry.historical_topology_mentions)}]"
                ),
                f"docs_tree_contradiction = {str(entry.docs_tree_contradiction).lower()}",
                (
                    "historical_shape_dominates_design = "
                    f"{str(entry.historical_shape_dominates_design).lower()}"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageTopologyDriftReport) -> bool:
    if not PACKAGE_TOPOLOGY_DRIFT_PATH.exists():
        return False
    return PACKAGE_TOPOLOGY_DRIFT_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_topology_drift_report()
    failures = validate_package_topology_drift(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package topology drift report is up to date")
            return 0
        print("package topology drift report is stale; regenerate it")
        return 1
    PACKAGE_TOPOLOGY_DRIFT_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package topology drift report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package topology drift report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the topology drift report is stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
