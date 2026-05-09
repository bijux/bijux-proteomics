# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generated core-handbook surfaces for flagship benchmark asset review."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.benchmarks.workflow_generalization import (
    WorkflowGeneralizationReport,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    KnowledgeWorkflowFamily,
)

from bijux_proteomics_dev.release.governance.benchmark_review_support import (
    CORE_FOUNDATION_DIR,
    LAST_REVIEWED,
    REPO_ROOT,
    BenchmarkPackageBundle,
    artifact_inventory_by_path,
    build_generalization_report_map,
    iter_benchmark_package_bundles,
    package_sha256,
)

__all__ = [
    "BENCHMARK_ASSET_AUDIT_PATH",
    "BENCHMARK_INCOMPLETENESS_LEDGER_PATH",
    "BENCHMARK_LICENSING_PATH",
    "LINEAGE_DOC_PATHS",
    "BenchmarkAssetAuditEntry",
    "BenchmarkAssetSourceAudit",
    "BenchmarkIncompletenessEntry",
    "BenchmarkLicensingEntry",
    "build_benchmark_asset_audit",
    "build_benchmark_incompleteness_ledger",
    "build_benchmark_licensing_matrix",
    "run",
]


BENCHMARK_ASSET_AUDIT_PATH = CORE_FOUNDATION_DIR / "benchmark-asset-audit.md"
BENCHMARK_LICENSING_PATH = (
    CORE_FOUNDATION_DIR / "benchmark-licensing-and-redistribution.md"
)
BENCHMARK_INCOMPLETENESS_LEDGER_PATH = (
    CORE_FOUNDATION_DIR / "benchmark-incompleteness-ledger.md"
)
LINEAGE_DOC_PATHS = {
    KnowledgeWorkflowFamily.DDA: CORE_FOUNDATION_DIR / "dda-benchmark-lineage.md",
    KnowledgeWorkflowFamily.DIA: CORE_FOUNDATION_DIR / "dia-benchmark-lineage.md",
    KnowledgeWorkflowFamily.LFQ: CORE_FOUNDATION_DIR / "lfq-benchmark-lineage.md",
    KnowledgeWorkflowFamily.MULTIPLEX: CORE_FOUNDATION_DIR
    / "multiplex-benchmark-lineage.md",
    KnowledgeWorkflowFamily.PTM: CORE_FOUNDATION_DIR / "ptm-benchmark-lineage.md",
    KnowledgeWorkflowFamily.TARGETED: CORE_FOUNDATION_DIR
    / "targeted-benchmark-lineage.md",
}
_PRIMARY_ROLE_LABEL = "primary flagship package"
_COMPANION_ROLE_LABEL = "companion generalization package"


@dataclass(frozen=True)
class BenchmarkAssetSourceAudit:
    """One outsider-readable source trail inside a public benchmark package."""

    source_id: str
    public_source_name: str
    public_reference_url: str
    upstream_repo_source_path: str
    local_artifact_path: str
    local_sha256: str
    extraction_step: str
    derived_paths: tuple[str, ...]
    rebuild_command: str


@dataclass(frozen=True)
class BenchmarkAssetAuditEntry:
    """One audited public benchmark package root."""

    workflow_family: KnowledgeWorkflowFamily
    package_role: str
    package_id: str
    package_label: str
    package_root: str
    benchmark_id: str
    benchmark_title: str
    public_dataset_identity: str
    evidence_tier: BenchmarkEvidenceTier
    source_locator_manifest_path: str
    citation_manifest_path: str
    generated_boundary_path: str
    rebuild_instructions_path: str
    rebuild_command: str
    package_manifest_path: str
    artifact_inventory_path: str
    quality_sheet_path: str
    lifecycle_record_path: str
    support_files_present: bool
    source_rows: tuple[BenchmarkAssetSourceAudit, ...]
    audit_note: str


@dataclass(frozen=True)
class BenchmarkLicensingEntry:
    """One package-level licensing and redistribution posture row."""

    workflow_family: KnowledgeWorkflowFamily
    package_role: str
    package_id: str
    package_root: str
    dataset_license_and_reuse_note: str
    known_license_limits: tuple[str, ...]
    source_license_notes: tuple[str, ...]
    redistributed_artifact_paths: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkIncompletenessEntry:
    """One package-level record of what still keeps the benchmark bounded."""

    workflow_family: KnowledgeWorkflowFamily
    package_role: str
    package_id: str
    package_root: str
    quality_blockers: tuple[str, ...]
    weakness_notes: tuple[str, ...]
    fixture_realism_limits: tuple[str, ...]
    expected_failure_conditions: tuple[str, ...]
    non_transfer_zones: tuple[str, ...]
    obsolescence_conditions: tuple[str, ...]


def _support_paths(bundle: BenchmarkPackageBundle) -> tuple[str, ...]:
    return (
        bundle.benchmark_manifest_path,
        bundle.artifact_inventory_path,
        bundle.quality_sheet_path,
        bundle.lifecycle_record_path,
        bundle.source_locator_manifest_path,
        bundle.citation_manifest_path,
        bundle.generated_boundary_path,
        bundle.rebuild_instructions_path,
    )


def _source_rows(bundle: BenchmarkPackageBundle) -> tuple[BenchmarkAssetSourceAudit, ...]:
    rows: list[BenchmarkAssetSourceAudit] = []
    inventory = artifact_inventory_by_path(bundle)
    derived_paths = _support_paths(bundle)
    for source in bundle.asset_root_entry.remote_sources:
        local_sha256 = inventory.get(source.local_artifact_path)
        rows.append(
            BenchmarkAssetSourceAudit(
                source_id=source.source_id,
                public_source_name=source.public_source_name,
                public_reference_url=source.public_reference_url,
                upstream_repo_source_path=source.upstream_repo_source_path,
                local_artifact_path=source.local_artifact_path,
                local_sha256=(
                    local_sha256.sha256
                    if local_sha256 is not None
                    else package_sha256(source.local_artifact_path)
                ),
                extraction_step=(
                    "Copy the tracked snapshot from "
                    f"`{source.upstream_repo_source_path}` into "
                    f"`{source.local_artifact_path}`, then rerun the package refresh "
                    "command so the derived metadata stays in sync."
                ),
                derived_paths=derived_paths,
                rebuild_command=bundle.rebuild_command,
            )
        )
    return tuple(rows)


def build_benchmark_asset_audit() -> tuple[BenchmarkAssetAuditEntry, ...]:
    """Audit every public benchmark package root for outsider-readable lineage."""

    entries: list[BenchmarkAssetAuditEntry] = []
    for bundle in iter_benchmark_package_bundles():
        support_files_present = all((REPO_ROOT / path).exists() for path in _support_paths(bundle))
        role_label = (
            _PRIMARY_ROLE_LABEL if bundle.package_role == "primary" else _COMPANION_ROLE_LABEL
        )
        entries.append(
            BenchmarkAssetAuditEntry(
                workflow_family=bundle.workflow_family,
                package_role=role_label,
                package_id=bundle.package_id,
                package_label=bundle.package_label,
                package_root=bundle.package_root,
                benchmark_id=bundle.benchmark_manifest.benchmark_id,
                benchmark_title=bundle.benchmark_manifest.title,
                public_dataset_identity=bundle.public_dataset_identity,
                evidence_tier=bundle.benchmark_manifest.evidence_tier,
                source_locator_manifest_path=bundle.source_locator_manifest_path,
                citation_manifest_path=bundle.citation_manifest_path,
                generated_boundary_path=bundle.generated_boundary_path,
                rebuild_instructions_path=bundle.rebuild_instructions_path,
                rebuild_command=bundle.rebuild_command,
                package_manifest_path=bundle.benchmark_manifest_path,
                artifact_inventory_path=bundle.artifact_inventory_path,
                quality_sheet_path=bundle.quality_sheet_path,
                lifecycle_record_path=bundle.lifecycle_record_path,
                support_files_present=support_files_present,
                source_rows=_source_rows(bundle),
                audit_note=(
                    "The audit keeps raw source, checksum, extraction step, derived review paths, "
                    "and the owning rebuild command visible without leaving the repository."
                ),
            )
        )
    return tuple(entries)


def build_benchmark_licensing_matrix() -> tuple[BenchmarkLicensingEntry, ...]:
    """Return the public licensing and redistribution posture for each package."""

    entries: list[BenchmarkLicensingEntry] = []
    for bundle in iter_benchmark_package_bundles():
        role_label = (
            _PRIMARY_ROLE_LABEL if bundle.package_role == "primary" else _COMPANION_ROLE_LABEL
        )
        redistributed_artifact_paths = tuple(
            asset.path
            for asset in bundle.source_assets
            if "/evidence/" in asset.path
            or "/primary/" in asset.path
            or "/comparator/" in asset.path
            or "/follow_up/" in asset.path
        )
        entries.append(
            BenchmarkLicensingEntry(
                workflow_family=bundle.workflow_family,
                package_role=role_label,
                package_id=bundle.package_id,
                package_root=bundle.package_root,
                dataset_license_and_reuse_note=bundle.benchmark_manifest.dataset_license_and_reuse_note,
                known_license_limits=bundle.asset_root_entry.known_license_limits,
                source_license_notes=tuple(
                    source.license_note for source in bundle.asset_root_entry.remote_sources
                ),
                redistributed_artifact_paths=redistributed_artifact_paths,
            )
        )
    return tuple(entries)


def build_benchmark_incompleteness_ledger() -> tuple[BenchmarkIncompletenessEntry, ...]:
    """Return the explicit reasons benchmark roots still stay bounded."""

    entries: list[BenchmarkIncompletenessEntry] = []
    for bundle in iter_benchmark_package_bundles():
        role_label = (
            _PRIMARY_ROLE_LABEL if bundle.package_role == "primary" else _COMPANION_ROLE_LABEL
        )
        entries.append(
            BenchmarkIncompletenessEntry(
                workflow_family=bundle.workflow_family,
                package_role=role_label,
                package_id=bundle.package_id,
                package_root=bundle.package_root,
                quality_blockers=bundle.quality_sheet.exact_blockers,
                weakness_notes=bundle.benchmark_manifest.weakness_notes,
                fixture_realism_limits=bundle.benchmark_manifest.fixture_realism_limits,
                expected_failure_conditions=bundle.benchmark_manifest.expected_failure_conditions,
                non_transfer_zones=bundle.benchmark_manifest.non_transfer_zones,
                obsolescence_conditions=bundle.benchmark_manifest.obsolescence_conditions,
            )
        )
    return tuple(entries)


def _grouped_bundles() -> dict[KnowledgeWorkflowFamily, tuple[BenchmarkAssetAuditEntry, ...]]:
    grouped: dict[KnowledgeWorkflowFamily, list[BenchmarkAssetAuditEntry]] = {
        family: [] for family in LINEAGE_DOC_PATHS
    }
    for entry in build_benchmark_asset_audit():
        grouped[entry.workflow_family].append(entry)
    return {family: tuple(entries) for family, entries in grouped.items()}


def _workflow_header(workflow_family: KnowledgeWorkflowFamily) -> tuple[str, str]:
    titles = {
        KnowledgeWorkflowFamily.DDA: ("DDA Benchmark Lineage", "bijux-proteomics-core-docs"),
        KnowledgeWorkflowFamily.DIA: ("DIA Benchmark Lineage", "bijux-proteomics-core-docs"),
        KnowledgeWorkflowFamily.LFQ: ("LFQ Benchmark Lineage", "bijux-proteomics-core-docs"),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            "Multiplex Benchmark Lineage",
            "bijux-proteomics-core-docs",
        ),
        KnowledgeWorkflowFamily.PTM: ("PTM Benchmark Lineage", "bijux-proteomics-core-docs"),
        KnowledgeWorkflowFamily.TARGETED: (
            "Targeted Benchmark Lineage",
            "bijux-proteomics-core-docs",
        ),
    }
    return titles[workflow_family]


def _render_asset_audit(entries: tuple[BenchmarkAssetAuditEntry, ...]) -> str:
    lines = [
        "---",
        "title: Benchmark Asset Audit",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-core-docs",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Asset Audit",
        "",
        "This page re-audits every public benchmark asset root that carries flagship or family-generalization pressure. It keeps the outsider-findable raw source, copied checksum, extraction step, derived review paths, and owning rebuild command visible from one handbook page.",
        "",
        "## Coverage",
        "",
        "| workflow family | package role | package root | source count | support files present |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| "
            f"`{entry.workflow_family.value}` | {entry.package_role} | "
            f"`{entry.package_root}` | `{len(entry.source_rows)}` | "
            f"{'yes' if entry.support_files_present else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Package Audits",
            "",
        ]
    )
    for entry in entries:
        lines.extend(
            [
                f"### `{entry.workflow_family.value}`: {entry.package_label}",
                "",
                f"- package id: `{entry.package_id}`",
                f"- package role: {entry.package_role}",
                f"- benchmark title: {entry.benchmark_title}",
                f"- public dataset identity: {entry.public_dataset_identity}",
                f"- evidence tier: `{entry.evidence_tier.value}`",
                f"- package root: `{entry.package_root}`",
                f"- source locator manifest: `{entry.source_locator_manifest_path}`",
                f"- citation manifest: `{entry.citation_manifest_path}`",
                f"- generated boundary manifest: `{entry.generated_boundary_path}`",
                f"- rebuild instructions: `{entry.rebuild_instructions_path}`",
                f"- derived package manifest: `{entry.package_manifest_path}`",
                f"- derived artifact inventory: `{entry.artifact_inventory_path}`",
                f"- derived quality sheet: `{entry.quality_sheet_path}`",
                f"- derived lifecycle record: `{entry.lifecycle_record_path}`",
                "",
                "| source name | copied path | sha256 | tracked upstream source | rebuild command |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for source in entry.source_rows:
            lines.append(
                "| "
                f"{source.public_source_name} | `{source.local_artifact_path}` | "
                f"`{source.local_sha256}` | `{source.upstream_repo_source_path}` | "
                f"`{source.rebuild_command}` |"
            )
        lines.extend(
            [
                "",
                "Copied-source extraction discipline:",
                "",
            ]
        )
        for source in entry.source_rows:
            lines.append(f"- {source.extraction_step}")
        lines.extend(
            [
                "",
                f"{entry.audit_note}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_lineage_doc(
    workflow_family: KnowledgeWorkflowFamily,
    entries: tuple[BenchmarkAssetAuditEntry, ...],
    report: WorkflowGeneralizationReport,
) -> str:
    title, owner = _workflow_header(workflow_family)
    primary = next(entry for entry in entries if entry.package_role == _PRIMARY_ROLE_LABEL)
    companion = next(
        entry for entry in entries if entry.package_role == _COMPANION_ROLE_LABEL
    )
    lines = [
        "---",
        f"title: {title}",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        f"owner: {owner}",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        f"# {title}",
        "",
        f"The `{workflow_family.value}` family now has a two-root lineage instead of one convenient package story. This page ties the primary flagship package, the companion generalization package, and the cross-package drift report together so an outsider can follow the evidence chain from copied input to derived review surface.",
        "",
        "## Family Contract",
        "",
        f"- benchmark title: {primary.benchmark_title}",
        f"- public dataset identity: {primary.public_dataset_identity}",
        f"- dataset locator: `{primary.package_manifest_path}`",
        f"- evidence tier: `{primary.evidence_tier.value}`",
        f"- primary package root: `{primary.package_root}`",
        f"- companion package root: `{companion.package_root}`",
        f"- cross-package generalization report: `{report.artifact_path}`",
        "",
        "## Raw Source Trail",
        "",
    ]
    for entry in (primary, companion):
        lines.extend(
            [
                f"### {entry.package_role}",
                "",
            ]
        )
        for source in entry.source_rows:
            lines.extend(
                [
                    f"- {source.public_source_name} copies `{source.upstream_repo_source_path}` into `{source.local_artifact_path}`",
                    f"- checksum: `{source.local_sha256}`",
                    f"- public reference: `{source.public_reference_url}`",
                    f"- rebuild command: `{source.rebuild_command}`",
                ]
            )
        lines.append("")
    lines.extend(
        [
            "## Derived Review Surfaces",
            "",
            f"- primary package manifest: `{primary.package_manifest_path}`",
            f"- primary artifact inventory: `{primary.artifact_inventory_path}`",
            f"- primary quality sheet: `{primary.quality_sheet_path}`",
            f"- companion package manifest: `{companion.package_manifest_path}`",
            f"- companion artifact inventory: `{companion.artifact_inventory_path}`",
            f"- companion quality sheet: `{companion.quality_sheet_path}`",
            f"- family drift report: `{report.artifact_path}`",
            "",
            "## What This Lineage Does And Does Not Prove",
            "",
            f"- primary claim scope: {primary.package_label} keeps `{workflow_family.value}` review grounded in `{primary.package_root}` rather than abstract benchmark prose.",
            f"- companion claim scope: {companion.package_label} exists to show where `{workflow_family.value}` family transfer weakens, not to hide that drift.",
            f"- current cross-package note: {report.note}",
            "",
            "## Rebuild Order",
            "",
            f"1. Refresh the primary root with `{primary.rebuild_command}`.",
            f"2. Refresh the companion root with `{companion.rebuild_command}`.",
            "3. Re-read the family drift report before strengthening any workflow-family sentence.",
        ]
    )
    return "\n".join(lines)


def _render_licensing_matrix(entries: tuple[BenchmarkLicensingEntry, ...]) -> str:
    lines = [
        "---",
        "title: Benchmark Licensing and Redistribution",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-core-docs",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Licensing and Redistribution",
        "",
        "This page makes the current licensing and redistribution posture explicit for every public benchmark root. It exists so a reviewer can tell the difference between what the repository redistributes as governed evidence and what remains only a public reference or external-engine context.",
        "",
        "## Package Matrix",
        "",
        "| workflow family | package role | redistributed evidence count | package root |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| "
            f"`{entry.workflow_family.value}` | {entry.package_role} | "
            f"`{len(entry.redistributed_artifact_paths)}` | `{entry.package_root}` |"
        )
    lines.extend(
        [
            "",
            "## Licensing Stories",
            "",
        ]
    )
    for entry in entries:
        lines.extend(
            [
                f"### `{entry.workflow_family.value}`: {entry.package_role}",
                "",
                f"- package id: `{entry.package_id}`",
                f"- package root: `{entry.package_root}`",
                f"- dataset reuse note: {entry.dataset_license_and_reuse_note}",
                "",
                "Redistributed evidence inside the package root:",
                "",
            ]
        )
        for path in entry.redistributed_artifact_paths:
            lines.append(f"- `{path}`")
        lines.extend(
            [
                "",
                "Current licensing limits:",
                "",
            ]
        )
        for note in entry.known_license_limits:
            lines.append(f"- {note}")
        for note in entry.source_license_notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def _render_incompleteness_ledger(
    entries: tuple[BenchmarkIncompletenessEntry, ...],
) -> str:
    lines = [
        "---",
        "title: Benchmark Incompleteness Ledger",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-core-docs",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Incompleteness Ledger",
        "",
        "This ledger records why the current benchmark roots still cap public trust language. It is intentionally repetitive: each package repeats its live blockers, realism limits, failure conditions, and non-transfer zones so a reviewer does not need to infer those limits from prose alone.",
        "",
        "## Package Summary",
        "",
        "| workflow family | package role | quality blockers | non-transfer zones |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| "
            f"`{entry.workflow_family.value}` | {entry.package_role} | "
            f"`{len(entry.quality_blockers)}` | `{len(entry.non_transfer_zones)}` |"
        )
    lines.extend(
        [
            "",
            "## Live Incompleteness Entries",
            "",
        ]
    )
    for entry in entries:
        lines.extend(
            [
                f"### `{entry.workflow_family.value}`: {entry.package_role}",
                "",
                f"- package id: `{entry.package_id}`",
                f"- package root: `{entry.package_root}`",
                "",
                "Quality blockers:",
                "",
            ]
        )
        for item in entry.quality_blockers:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "Weakness notes:",
                "",
            ]
        )
        for item in entry.weakness_notes:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "Fixture realism limits:",
                "",
            ]
        )
        for item in entry.fixture_realism_limits:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "Expected failure conditions:",
                "",
            ]
        )
        for item in entry.expected_failure_conditions:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "Non-transfer zones:",
                "",
            ]
        )
        for item in entry.non_transfer_zones:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "Obsolescence conditions:",
                "",
            ]
        )
        for item in entry.obsolescence_conditions:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _write_text(path: Path, text: str) -> int:
    rendered = text.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return 0
    path.write_text(rendered, encoding="utf-8")
    return 1


def run(*, check: bool = False) -> int:
    """Write or verify the benchmark asset audit and family lineage pages."""

    audit_entries = build_benchmark_asset_audit()
    licensing_entries = build_benchmark_licensing_matrix()
    incompleteness_entries = build_benchmark_incompleteness_ledger()
    grouped = _grouped_bundles()
    reports = build_generalization_report_map()

    rendered: dict[Path, str] = {
        BENCHMARK_ASSET_AUDIT_PATH: _render_asset_audit(audit_entries),
        BENCHMARK_LICENSING_PATH: _render_licensing_matrix(licensing_entries),
        BENCHMARK_INCOMPLETENESS_LEDGER_PATH: _render_incompleteness_ledger(
            incompleteness_entries
        ),
    }
    for workflow_family, path in LINEAGE_DOC_PATHS.items():
        rendered[path] = _render_lineage_doc(
            workflow_family,
            grouped[workflow_family],
            reports[workflow_family.value],
        )

    changed = 0
    for path, text in rendered.items():
        rendered_text = text.rstrip() + "\n"
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered_text:
                return 1
            continue
        changed += _write_text(path, text)
    return 0 if check or changed >= 0 else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijux-proteomics benchmark-asset-governance",
        description=(
            "Generate or verify benchmark asset audit and family lineage handbook pages."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the checked-in handbook pages match generated content",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return run(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
