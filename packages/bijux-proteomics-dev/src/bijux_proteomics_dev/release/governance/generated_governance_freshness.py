from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
import re

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_foundation.testing.generated_file_markers import (
    GeneratedFileMarkerKind,
    detect_generated_file_marker,
)

__all__ = [
    "GeneratedGovernanceFreshnessEntry",
    "GeneratedGovernanceFreshnessIssue",
    "GeneratedGovernanceFreshnessReport",
    "build_generated_governance_freshness_report",
    "validate_generated_governance_freshness",
]


PACKAGE_GOVERNANCE_DIR = REPO_ROOT / "configs" / "package-governance"
REGENERATE_PATTERN = re.compile(
    r"^# Regenerate with: \./\.venv/bin/python -m (?P<module>[a-zA-Z0-9_\\.]+)$"
)


@dataclass(frozen=True)
class GeneratedGovernanceFreshnessEntry:
    """Freshness status for one generated governance report."""

    relative_path: str
    module_name: str
    fresh: bool


@dataclass(frozen=True)
class GeneratedGovernanceFreshnessReport:
    """Freshness report for generated governance files."""

    entries: tuple[GeneratedGovernanceFreshnessEntry, ...]


@dataclass(frozen=True)
class GeneratedGovernanceFreshnessIssue:
    """One issue in the generated governance freshness contract."""

    code: str
    detail: str


def _generated_governance_paths() -> tuple[Path, ...]:
    paths: list[Path] = []
    for path in sorted(PACKAGE_GOVERNANCE_DIR.rglob("*.toml")):
        marker = detect_generated_file_marker(path)
        if (
            marker is not None
            and marker.kind == GeneratedFileMarkerKind.GENERATED_HEADER
        ):
            paths.append(path)
    return tuple(paths)


def _module_name(path: Path) -> str | None:
    marker = detect_generated_file_marker(path)
    if marker is None or marker.regenerate_command is None:
        return None
    match = REGENERATE_PATTERN.match(f"# Regenerate with: {marker.regenerate_command}")
    if match is None:
        return None
    return match.group("module")


def _run_check(module_name: str) -> bool:
    module = importlib.import_module(module_name)
    run = getattr(module, "run", None)
    if not callable(run):
        raise AttributeError(f"{module_name} does not expose run(check=True)")
    result = run(check=True)
    return isinstance(result, int) and result == 0


def build_generated_governance_freshness_report() -> GeneratedGovernanceFreshnessReport:
    """Build the freshness report for every generated governance file."""

    entries: list[GeneratedGovernanceFreshnessEntry] = []
    freshness_cache: dict[str, bool] = {}
    for path in _generated_governance_paths():
        module_name = _module_name(path)
        if module_name is None:
            entries.append(
                GeneratedGovernanceFreshnessEntry(
                    relative_path=path.relative_to(REPO_ROOT).as_posix(),
                    module_name="",
                    fresh=False,
                )
            )
            continue
        if module_name not in freshness_cache:
            freshness_cache[module_name] = _run_check(module_name)
        entries.append(
            GeneratedGovernanceFreshnessEntry(
                relative_path=path.relative_to(REPO_ROOT).as_posix(),
                module_name=module_name,
                fresh=freshness_cache[module_name],
            )
        )
    return GeneratedGovernanceFreshnessReport(entries=tuple(entries))


def validate_generated_governance_freshness() -> tuple[
    GeneratedGovernanceFreshnessIssue, ...
]:
    """Validate that every generated governance file has a working freshness lane."""

    issues: list[GeneratedGovernanceFreshnessIssue] = []
    report = build_generated_governance_freshness_report()
    for entry in report.entries:
        if not entry.module_name:
            issues.append(
                GeneratedGovernanceFreshnessIssue(
                    code="missing-regenerate-command",
                    detail=(
                        f"{entry.relative_path} is marked generated but does not expose a governed regenerate command"
                    ),
                )
            )
            continue
        if not entry.fresh:
            issues.append(
                GeneratedGovernanceFreshnessIssue(
                    code="stale-generated-governance-report",
                    detail=f"{entry.relative_path} is stale under {entry.module_name}",
                )
            )
    return tuple(issues)
