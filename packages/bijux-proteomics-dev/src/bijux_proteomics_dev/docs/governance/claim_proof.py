from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_docs,
    package_test_modules,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_DOCS_CLAIM_PROOF_PATH",
    "MONITORED_CLAIM_PROOF_FAMILIES",
    "PackageDocsClaimProofEntry",
    "PackageDocsClaimProofGuard",
    "PackageDocsClaimProofReport",
    "build_package_docs_claim_proof_report",
    "run",
    "validate_package_docs_claim_proof",
]


PACKAGE_DOCS_CLAIM_PROOF_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-docs-claim-proof.toml"
)
MONITORED_CLAIM_PROOF_FAMILIES = {
    "benchmark": ("benchmark", "performance"),
    "replay": ("replay",),
    "integrity": ("integrity",),
}


@dataclass(frozen=True)
class PackageDocsClaimProofEntry:
    """Proof-bearing documentation claims for one package."""

    distribution_name: str
    benchmark_claim_count: int
    benchmark_proof_artifact_count: int
    replay_claim_count: int
    replay_proof_artifact_count: int
    integrity_claim_count: int
    integrity_proof_artifact_count: int
    benchmark_proof_artifacts_per_claim: float
    replay_proof_artifacts_per_claim: float
    integrity_proof_artifacts_per_claim: float
    benchmark_claim_document_paths: tuple[str, ...]
    benchmark_proof_artifact_paths: tuple[str, ...]
    replay_claim_document_paths: tuple[str, ...]
    replay_proof_artifact_paths: tuple[str, ...]
    integrity_claim_document_paths: tuple[str, ...]
    integrity_proof_artifact_paths: tuple[str, ...]
    unproven_claim_kinds: tuple[str, ...]


@dataclass(frozen=True)
class PackageDocsClaimProofGuard:
    """Release-blocking guardrails over proof-bearing doc claims."""

    max_total_unproven_claim_kind_count: int
    min_total_benchmark_proof_artifact_count: int
    min_total_replay_proof_artifact_count: int
    min_total_integrity_proof_artifact_count: int


@dataclass(frozen=True)
class PackageDocsClaimProofReport:
    """Checked docs claim-versus-proof report across repository packages."""

    entries: tuple[PackageDocsClaimProofEntry, ...]
    guard: PackageDocsClaimProofGuard


def _proof_artifact_count(package_name: str, proof_tokens: tuple[str, ...]) -> int:
    return sum(
        any(token in path.as_posix().lower() for token in proof_tokens)
        for path in package_test_modules(package_name)
    )


def _matching_repo_relative_paths(
    paths: tuple[Path, ...],
    tokens: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in paths
        if any(token in path.as_posix().lower() for token in tokens)
    )


def _claim_document_paths(
    paths: tuple[Path, ...], tokens: tuple[str, ...]
) -> tuple[str, ...]:
    matched_paths: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        if any(token in text for token in tokens):
            matched_paths.append(path.relative_to(REPO_ROOT).as_posix())
    return tuple(matched_paths)


def _proof_ratio(claim_count: int, proof_count: int) -> float:
    if claim_count <= 0:
        return 0.0
    return round(proof_count / claim_count, 4)


def build_package_docs_claim_proof_report() -> PackageDocsClaimProofReport:
    """Build the checked docs claim-versus-proof report."""

    entries: list[PackageDocsClaimProofEntry] = []
    for package_name in workspace_package_names():
        docs_paths = package_docs(package_name)
        test_paths = package_test_modules(package_name)
        benchmark_claim_document_paths = _claim_document_paths(
            docs_paths,
            MONITORED_CLAIM_PROOF_FAMILIES["benchmark"],
        )
        benchmark_claim_count = len(benchmark_claim_document_paths)
        benchmark_proof_artifact_count = _proof_artifact_count(
            package_name,
            MONITORED_CLAIM_PROOF_FAMILIES["benchmark"],
        )
        replay_claim_document_paths = _claim_document_paths(
            docs_paths,
            MONITORED_CLAIM_PROOF_FAMILIES["replay"],
        )
        replay_claim_count = len(replay_claim_document_paths)
        replay_proof_artifact_count = _proof_artifact_count(
            package_name,
            MONITORED_CLAIM_PROOF_FAMILIES["replay"],
        )
        integrity_claim_document_paths = _claim_document_paths(
            docs_paths,
            MONITORED_CLAIM_PROOF_FAMILIES["integrity"],
        )
        integrity_claim_count = len(integrity_claim_document_paths)
        integrity_proof_artifact_count = _proof_artifact_count(
            package_name,
            MONITORED_CLAIM_PROOF_FAMILIES["integrity"],
        )
        benchmark_proof_artifact_paths = _matching_repo_relative_paths(
            test_paths,
            MONITORED_CLAIM_PROOF_FAMILIES["benchmark"],
        )
        replay_proof_artifact_paths = _matching_repo_relative_paths(
            test_paths,
            MONITORED_CLAIM_PROOF_FAMILIES["replay"],
        )
        integrity_proof_artifact_paths = _matching_repo_relative_paths(
            test_paths,
            MONITORED_CLAIM_PROOF_FAMILIES["integrity"],
        )
        unproven_claim_kinds = tuple(
            claim_kind
            for claim_kind, claim_count, proof_count in (
                ("benchmark", benchmark_claim_count, benchmark_proof_artifact_count),
                ("replay", replay_claim_count, replay_proof_artifact_count),
                ("integrity", integrity_claim_count, integrity_proof_artifact_count),
            )
            if claim_count > 0 and proof_count == 0
        )
        entries.append(
            PackageDocsClaimProofEntry(
                distribution_name=package_name,
                benchmark_claim_count=benchmark_claim_count,
                benchmark_proof_artifact_count=benchmark_proof_artifact_count,
                replay_claim_count=replay_claim_count,
                replay_proof_artifact_count=replay_proof_artifact_count,
                integrity_claim_count=integrity_claim_count,
                integrity_proof_artifact_count=integrity_proof_artifact_count,
                benchmark_proof_artifacts_per_claim=_proof_ratio(
                    benchmark_claim_count,
                    benchmark_proof_artifact_count,
                ),
                replay_proof_artifacts_per_claim=_proof_ratio(
                    replay_claim_count,
                    replay_proof_artifact_count,
                ),
                integrity_proof_artifacts_per_claim=_proof_ratio(
                    integrity_claim_count,
                    integrity_proof_artifact_count,
                ),
                benchmark_claim_document_paths=benchmark_claim_document_paths,
                benchmark_proof_artifact_paths=benchmark_proof_artifact_paths,
                replay_claim_document_paths=replay_claim_document_paths,
                replay_proof_artifact_paths=replay_proof_artifact_paths,
                integrity_claim_document_paths=integrity_claim_document_paths,
                integrity_proof_artifact_paths=integrity_proof_artifact_paths,
                unproven_claim_kinds=unproven_claim_kinds,
            )
        )
    return PackageDocsClaimProofReport(
        entries=tuple(entries),
        guard=PackageDocsClaimProofGuard(
            max_total_unproven_claim_kind_count=sum(
                len(entry.unproven_claim_kinds) for entry in entries
            ),
            min_total_benchmark_proof_artifact_count=sum(
                entry.benchmark_proof_artifact_count for entry in entries
            ),
            min_total_replay_proof_artifact_count=sum(
                entry.replay_proof_artifact_count for entry in entries
            ),
            min_total_integrity_proof_artifact_count=sum(
                entry.integrity_proof_artifact_count for entry in entries
            ),
        ),
    )


def _load_package_docs_claim_proof_report(
    path: Path,
) -> PackageDocsClaimProofReport | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    guard_data = data["guard"]
    entries = []
    for item in data["package"]:
        entries.append(
            PackageDocsClaimProofEntry(
                distribution_name=item["distribution_name"],
                benchmark_claim_count=int(item["benchmark_claim_count"]),
                benchmark_proof_artifact_count=int(
                    item["benchmark_proof_artifact_count"]
                ),
                replay_claim_count=int(item["replay_claim_count"]),
                replay_proof_artifact_count=int(item["replay_proof_artifact_count"]),
                integrity_claim_count=int(item["integrity_claim_count"]),
                integrity_proof_artifact_count=int(
                    item["integrity_proof_artifact_count"]
                ),
                benchmark_proof_artifacts_per_claim=float(
                    item.get("benchmark_proof_artifacts_per_claim", 0.0)
                ),
                replay_proof_artifacts_per_claim=float(
                    item.get("replay_proof_artifacts_per_claim", 0.0)
                ),
                integrity_proof_artifacts_per_claim=float(
                    item.get("integrity_proof_artifacts_per_claim", 0.0)
                ),
                benchmark_claim_document_paths=tuple(
                    item.get("benchmark_claim_document_paths", [])
                ),
                benchmark_proof_artifact_paths=tuple(
                    item.get("benchmark_proof_artifact_paths", [])
                ),
                replay_claim_document_paths=tuple(
                    item.get("replay_claim_document_paths", [])
                ),
                replay_proof_artifact_paths=tuple(
                    item.get("replay_proof_artifact_paths", [])
                ),
                integrity_claim_document_paths=tuple(
                    item.get("integrity_claim_document_paths", [])
                ),
                integrity_proof_artifact_paths=tuple(
                    item.get("integrity_proof_artifact_paths", [])
                ),
                unproven_claim_kinds=tuple(item["unproven_claim_kinds"]),
            )
        )
    return PackageDocsClaimProofReport(
        entries=tuple(entries),
        guard=PackageDocsClaimProofGuard(
            max_total_unproven_claim_kind_count=int(
                guard_data["max_total_unproven_claim_kind_count"]
            ),
            min_total_benchmark_proof_artifact_count=int(
                guard_data["min_total_benchmark_proof_artifact_count"]
            ),
            min_total_replay_proof_artifact_count=int(
                guard_data["min_total_replay_proof_artifact_count"]
            ),
            min_total_integrity_proof_artifact_count=int(
                guard_data["min_total_integrity_proof_artifact_count"]
            ),
        ),
    )


def validate_package_docs_claim_proof(
    report: PackageDocsClaimProofReport | None = None,
) -> tuple[str, ...]:
    """Fail release when proof-bearing doc claims outrun repository evidence."""

    report = report or build_package_docs_claim_proof_report()
    baseline = _load_package_docs_claim_proof_report(PACKAGE_DOCS_CLAIM_PROOF_PATH)
    baseline = baseline or report
    failures: list[str] = []
    total_unproven_claim_kind_count = sum(
        len(entry.unproven_claim_kinds) for entry in report.entries
    )
    total_benchmark_proof_artifact_count = sum(
        entry.benchmark_proof_artifact_count for entry in report.entries
    )
    total_replay_proof_artifact_count = sum(
        entry.replay_proof_artifact_count for entry in report.entries
    )
    total_integrity_proof_artifact_count = sum(
        entry.integrity_proof_artifact_count for entry in report.entries
    )
    if (
        total_unproven_claim_kind_count
        > baseline.guard.max_total_unproven_claim_kind_count
    ):
        failures.append(
            "doc claim-versus-proof gaps grew beyond the governed evidence baseline"
        )
    if (
        total_benchmark_proof_artifact_count
        < baseline.guard.min_total_benchmark_proof_artifact_count
    ):
        failures.append(
            "benchmark proof artifacts dropped below the governed docs evidence baseline"
        )
    if (
        total_replay_proof_artifact_count
        < baseline.guard.min_total_replay_proof_artifact_count
    ):
        failures.append(
            "replay proof artifacts dropped below the governed docs evidence baseline"
        )
    if (
        total_integrity_proof_artifact_count
        < baseline.guard.min_total_integrity_proof_artifact_count
    ):
        failures.append(
            "integrity proof artifacts dropped below the governed docs evidence baseline"
        )
    baseline_entries = {entry.distribution_name: entry for entry in baseline.entries}
    for entry in report.entries:
        baseline_entry = baseline_entries.get(entry.distribution_name)
        if baseline_entry is None:
            continue
        for claim_kind in ("benchmark", "replay", "integrity"):
            current_claim_count = getattr(entry, f"{claim_kind}_claim_count")
            current_proof_count = getattr(entry, f"{claim_kind}_proof_artifact_count")
            current_ratio = getattr(entry, f"{claim_kind}_proof_artifacts_per_claim")
            baseline_proof_count = getattr(
                baseline_entry,
                f"{claim_kind}_proof_artifact_count",
            )
            baseline_ratio = getattr(
                baseline_entry,
                f"{claim_kind}_proof_artifacts_per_claim",
            )
            if current_claim_count <= 0:
                continue
            if current_proof_count < baseline_proof_count:
                failures.append(
                    f"{entry.distribution_name} lost {claim_kind} proof artifacts "
                    "relative to the checked-in package baseline"
                )
            if current_ratio < baseline_ratio:
                failures.append(
                    f"{entry.distribution_name} weakened {claim_kind} proof coverage "
                    "relative to the checked-in package baseline"
                )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _render_float(value: float) -> str:
    return f"{value:.4f}"


def _toml_text(report: PackageDocsClaimProofReport) -> str:
    lines = [
        "# Generated package docs claim-versus-proof report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.docs.governance.claim_proof",
        "",
        "[guard]",
        (
            "max_total_unproven_claim_kind_count = "
            f"{report.guard.max_total_unproven_claim_kind_count}"
        ),
        (
            "min_total_benchmark_proof_artifact_count = "
            f"{report.guard.min_total_benchmark_proof_artifact_count}"
        ),
        (
            "min_total_replay_proof_artifact_count = "
            f"{report.guard.min_total_replay_proof_artifact_count}"
        ),
        (
            "min_total_integrity_proof_artifact_count = "
            f"{report.guard.min_total_integrity_proof_artifact_count}"
        ),
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"benchmark_claim_count = {entry.benchmark_claim_count}",
                (
                    "benchmark_proof_artifact_count = "
                    f"{entry.benchmark_proof_artifact_count}"
                ),
                f"replay_claim_count = {entry.replay_claim_count}",
                f"replay_proof_artifact_count = {entry.replay_proof_artifact_count}",
                f"integrity_claim_count = {entry.integrity_claim_count}",
                (
                    "integrity_proof_artifact_count = "
                    f"{entry.integrity_proof_artifact_count}"
                ),
                (
                    "benchmark_proof_artifacts_per_claim = "
                    f"{_render_float(entry.benchmark_proof_artifacts_per_claim)}"
                ),
                (
                    "replay_proof_artifacts_per_claim = "
                    f"{_render_float(entry.replay_proof_artifacts_per_claim)}"
                ),
                (
                    "integrity_proof_artifacts_per_claim = "
                    f"{_render_float(entry.integrity_proof_artifacts_per_claim)}"
                ),
                (
                    "benchmark_claim_document_paths = "
                    f"[{_render_tuple(entry.benchmark_claim_document_paths)}]"
                ),
                (
                    "benchmark_proof_artifact_paths = "
                    f"[{_render_tuple(entry.benchmark_proof_artifact_paths)}]"
                ),
                (
                    "replay_claim_document_paths = "
                    f"[{_render_tuple(entry.replay_claim_document_paths)}]"
                ),
                (
                    "replay_proof_artifact_paths = "
                    f"[{_render_tuple(entry.replay_proof_artifact_paths)}]"
                ),
                (
                    "integrity_claim_document_paths = "
                    f"[{_render_tuple(entry.integrity_claim_document_paths)}]"
                ),
                (
                    "integrity_proof_artifact_paths = "
                    f"[{_render_tuple(entry.integrity_proof_artifact_paths)}]"
                ),
                f"unproven_claim_kinds = [{_render_tuple(entry.unproven_claim_kinds)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageDocsClaimProofReport) -> bool:
    if not PACKAGE_DOCS_CLAIM_PROOF_PATH.exists():
        return False
    return PACKAGE_DOCS_CLAIM_PROOF_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_docs_claim_proof_report()
    failures = validate_package_docs_claim_proof(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package docs claim-versus-proof report is up to date")
            return 0
        print("package docs claim-versus-proof report is stale; regenerate it")
        return 1
    PACKAGE_DOCS_CLAIM_PROOF_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package docs claim-versus-proof report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package docs claim-versus-proof report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package docs claim-versus-proof report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
