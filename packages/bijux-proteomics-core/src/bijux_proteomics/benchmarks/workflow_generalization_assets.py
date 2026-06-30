# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Commands that refresh companion benchmark packages and generalization reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bijux_proteomics.benchmarks.flagship.public_packages import (
    FlagshipPublicBenchmarkPackage,
)
from bijux_proteomics.benchmarks.workflow_generalization import (
    SecondaryPublicPackageAssetRegistry,
    WorkflowFamilyStabilityScorecard,
    WorkflowGeneralizationReport,
    build_secondary_public_package_artifact_inventories,
    build_secondary_public_package_asset_registry,
    build_secondary_public_package_lifecycle_records,
    build_secondary_public_package_quality_sheets,
    build_workflow_family_stability_scorecard,
    build_workflow_generalization_reports,
    list_secondary_public_benchmark_packages,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _write_text(path: Path, payload: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")
    return str(path.relative_to(_repo_root()))


def _package_readme(package: FlagshipPublicBenchmarkPackage) -> str:
    lines = [
        f"# {package.package_label}",
        "",
        package.note,
        "",
        "Tracked package evidence:",
        "",
    ]
    for asset in package.source_assets:
        if asset.path.endswith(
            (
                "package_manifest.json",
                "artifact_inventory.json",
                "quality_sheet.json",
                "lifecycle.json",
                "source_locator_manifest.json",
                "citation_manifest.json",
                "generated_boundary.json",
                "rebuild_instructions.md",
                "README.md",
            )
        ):
            continue
        relative = asset.path.replace(f"{package.package_root}/", "")
        lines.append(f"- `{relative}`")
    lines.extend(
        (
            "",
            "Tracked package metadata lives beside this file:",
            "",
            "- `source_locator_manifest.json`",
            "- `citation_manifest.json`",
            "- `generated_boundary.json`",
            "- `rebuild_instructions.md`",
            "- `package_manifest.json`",
            "- `artifact_inventory.json`",
            "- `quality_sheet.json`",
            "- `lifecycle.json`",
            "",
            "This companion package exists to pressure family-level transfer beyond the single primary flagship package.",
        )
    )
    return "\n".join(lines)


def _write_registry_support_files(
    registry: SecondaryPublicPackageAssetRegistry,
) -> tuple[str, ...]:
    repo_root = _repo_root()
    written: list[str] = []
    written.append(
        _write_text(
            repo_root / registry.artifact_path,
            registry.to_stable_json(),
        )
    )
    for entry in registry.entries:
        source_locator_path = repo_root / entry.source_locator_manifest_path
        citation_manifest_path = repo_root / entry.citation_manifest_path
        generated_boundary_path = repo_root / entry.generated_boundary_path
        rebuild_instructions_path = repo_root / entry.rebuild_instructions_path
        source_locator_path.write_text(
            json.dumps(
                {
                    "package_id": entry.package_id,
                    "workflow_family": entry.workflow_family,
                    "asset_root": entry.asset_root,
                    "remote_sources": [
                        source.model_dump(mode="json")
                        for source in entry.remote_sources
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        citation_manifest_path.write_text(
            json.dumps(
                {
                    "package_id": entry.package_id,
                    "workflow_family": entry.workflow_family,
                    "citations": [
                        citation.model_dump(mode="json") for citation in entry.citations
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        generated_boundary_path.write_text(
            json.dumps(
                {
                    "package_id": entry.package_id,
                    "workflow_family": entry.workflow_family,
                    "generated_boundaries": [
                        boundary.model_dump(mode="json")
                        for boundary in entry.generated_boundaries
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        rebuild_instructions_path.write_text(
            "\n".join(
                (
                    f"# Rebuild {entry.workflow_family.upper()} Companion Package",
                    "",
                    f"Asset root: `{entry.asset_root}`",
                    "",
                    "Rebuild discipline:",
                    "",
                    "- refresh copied snapshots from the tracked upstream repo paths in `source_locator_manifest.json`",
                    "- rerun the workflow generalization asset refresh command to regenerate package metadata and reports",
                    "",
                    "Command:",
                    "",
                    "```bash",
                    "uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh",
                    "```",
                    "",
                    f"Expected wall time: `{entry.expected_wall_time_minutes}` minutes",
                    f"Expected disk footprint: `{entry.expected_disk_footprint_mb}` MB",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        written.extend(
            (
                str(source_locator_path.relative_to(repo_root)),
                str(citation_manifest_path.relative_to(repo_root)),
                str(generated_boundary_path.relative_to(repo_root)),
                str(rebuild_instructions_path.relative_to(repo_root)),
            )
        )
    return tuple(written)


def _write_package_surfaces() -> tuple[str, ...]:
    repo_root = _repo_root()
    packages = {
        package.package_id: package
        for package in list_secondary_public_benchmark_packages()
    }
    quality_sheets = {
        sheet.package_id: sheet
        for sheet in build_secondary_public_package_quality_sheets()
    }
    lifecycle_records = {
        record.package_id: record
        for record in build_secondary_public_package_lifecycle_records()
    }
    written: list[str] = []
    for package_id, package in packages.items():
        written.append(
            _write_text(
                repo_root / package.benchmark_manifest_path, package.to_stable_json()
            )
        )
        written.append(
            _write_text(
                repo_root / quality_sheets[package_id].quality_path,
                quality_sheets[package_id].to_stable_json(),
            )
        )
        written.append(
            _write_text(
                repo_root / lifecycle_records[package_id].lifecycle_path,
                lifecycle_records[package_id].to_stable_json(),
            )
        )
        written.append(
            _write_text(
                repo_root / f"{package.package_root}/README.md",
                _package_readme(package),
            )
        )
    inventories = {
        inventory.package_id: inventory
        for inventory in build_secondary_public_package_artifact_inventories()
    }
    for package_id in packages:
        written.append(
            _write_text(
                repo_root / inventories[package_id].inventory_path,
                inventories[package_id].to_stable_json(),
            )
        )
    return tuple(written)


def _write_generalization_reports(
    reports: tuple[WorkflowGeneralizationReport, ...],
    scorecard: WorkflowFamilyStabilityScorecard,
) -> tuple[str, ...]:
    repo_root = _repo_root()
    written: list[str] = []
    for report in reports:
        written.append(
            _write_text(repo_root / report.artifact_path, report.to_stable_json())
        )
    written.append(
        _write_text(repo_root / scorecard.artifact_path, scorecard.to_stable_json())
    )
    return tuple(written)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijux-proteomics workflow-generalization-assets",
        description=(
            "Refresh companion public benchmark packages and cross-package generalization reports."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "refresh",
        help="rewrite companion package metadata, support files, generalization reports, and the stability scorecard",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command != "refresh":
        parser.error(f"unsupported command: {args.command}")
    written = list(
        _write_registry_support_files(build_secondary_public_package_asset_registry())
    )
    written.extend(_write_package_surfaces())
    written.extend(
        _write_generalization_reports(
            build_workflow_generalization_reports(),
            build_workflow_family_stability_scorecard(),
        )
    )
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
