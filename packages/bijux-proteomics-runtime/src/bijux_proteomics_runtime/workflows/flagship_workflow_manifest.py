"""Checked manifest for the flagship workflow chain the repository can defend."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_runtime.workflows.flagship_workflow_chain import (
    FlagshipWorkflowClaimTier,
    FlagshipWorkflowStage,
    build_flagship_workflow_scope_dossier,
)

__all__ = [
    "FLAGSHIP_WORKFLOW_MANIFEST_PATH",
    "FlagshipWorkflowManifest",
    "FlagshipWorkflowManifestIssue",
    "FlagshipWorkflowManifestStageEntry",
    "build_flagship_workflow_manifest",
    "run",
    "validate_flagship_workflow_manifest",
]


REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
FLAGSHIP_WORKFLOW_MANIFEST_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "flagship-workflow-manifest.toml"
)


@dataclass(frozen=True)
class FlagshipWorkflowManifestStageEntry:
    """One owner stage in the checked flagship workflow manifest."""

    stage: FlagshipWorkflowStage
    owner_package: str
    source_path: str
    test_path: str
    docs_path: str
    artifact_paths: tuple[str, ...]
    validating_test_ids: tuple[str, ...]


@dataclass(frozen=True)
class FlagshipWorkflowManifest:
    """Checked manifest for the flagship workflow chain."""

    workflow_id: str
    flagship_family_id: str
    builder_module: str
    builder_symbol: str
    docs_path: str
    owner_packages: tuple[str, ...]
    claim_taxonomy: tuple[str, ...]
    stages: tuple[FlagshipWorkflowManifestStageEntry, ...]


@dataclass(frozen=True)
class FlagshipWorkflowManifestIssue:
    """One manifest issue that blocks flagship workflow truth claims."""

    code: str
    detail: str


def build_flagship_workflow_manifest() -> FlagshipWorkflowManifest:
    """Build the checked manifest for the flagship workflow chain."""

    dossier = build_flagship_workflow_scope_dossier()
    return FlagshipWorkflowManifest(
        workflow_id="flagship-workflow-chain",
        flagship_family_id=dossier.flagship_family_id,
        builder_module="bijux_proteomics_runtime.workflows.flagship_workflow_chain",
        builder_symbol="build_flagship_workflow_chain",
        docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
        owner_packages=(
            "bijux-proteomics-runtime",
            "bijux-proteomics-core",
            "bijux-proteomics-knowledge",
            "bijux-proteomics-intelligence",
            "bijux-proteomics-lab",
        ),
        claim_taxonomy=tuple(tier.value for tier in dossier.claim_taxonomy),
        stages=(
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.SEQUENCE_INTAKE,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/sequence-to-digest/targets.fasta",
                    "artifacts/workflows/sequence-to-digest/decoys.fasta",
                    "artifacts/workflows/sequence-to-digest/peptides.tsv",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.SEARCH_AND_CONFIDENCE,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/dda-import/spectra.mgf",
                    "artifacts/workflows/dda-import/psm.tsv",
                    "artifacts/workflows/dda-import/protein_inference.tsv",
                    "artifacts/workflows/dda-import/qc_report.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.QUANTIFICATION,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/quant-runtime/matrix.tsv",
                    "artifacts/workflows/quant-runtime/normalization.json",
                    "artifacts/workflows/quant-runtime/differential_abundance.tsv",
                    "artifacts/workflows/quant-runtime/review_bundle.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.PTM_REVIEW,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/ptm-runtime/ptm_sites.tsv",
                    "artifacts/workflows/ptm-runtime/ptm_occupancy.tsv",
                    "artifacts/workflows/ptm-runtime/ptm_motif_windows.tsv",
                    "artifacts/workflows/ptm-runtime/ptm_lab_packet.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.SCIENTIFIC_KERNEL,
                owner_package="bijux-proteomics-core",
                source_path="packages/bijux-proteomics-core/src/bijux_proteomics/review/flagship_kernel.py",
                test_path="packages/bijux-proteomics-core/tests/review/test_flagship_scientific_kernel_surface.py",
                docs_path="packages/bijux-proteomics-core/README.md",
                artifact_paths=(
                    "artifacts/workflows/flagship-workflow-chain/core/scientific_kernel.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-core/tests/review/test_flagship_scientific_kernel_surface.py::test_build_flagship_scientific_kernel_report_exposes_narrow_scope_boundaries",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.EVIDENCE_REVIEW,
                owner_package="bijux-proteomics-knowledge",
                source_path="packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/reviews/flagship_evidence.py",
                test_path="packages/bijux-proteomics-knowledge/tests/reviews/test_flagship_evidence_surface.py",
                docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
                artifact_paths=(
                    "artifacts/workflows/flagship-workflow-chain/knowledge/decision_brief.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-knowledge/tests/reviews/test_flagship_evidence_surface.py::test_build_flagship_evidence_decision_brief_preserves_claim_tier_and_artifact_path",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.DECISION_REVIEW,
                owner_package="bijux-proteomics-intelligence",
                source_path="packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/judgment/flagship_decisions.py",
                test_path="packages/bijux-proteomics-intelligence/tests/judgment/test_flagship_decisions_surface.py",
                docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
                artifact_paths=(
                    "artifacts/workflows/flagship-workflow-chain/intelligence/decision_review.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-intelligence/tests/judgment/test_flagship_decisions_surface.py::test_build_flagship_decision_review_allows_lab_when_kernel_and_review_are_clean",
                    "packages/bijux-proteomics-intelligence/tests/judgment/test_flagship_decisions_surface.py::test_build_flagship_decision_review_keeps_downgrade_chain_visible",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.LAB_HANDOFF,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/lab-handoff/assay_plan.tsv",
                    "artifacts/workflows/lab-handoff/handoff_export.json",
                    "artifacts/workflows/lab-handoff/unresolved_risk_report.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
                ),
            ),
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage.FOLLOW_UP,
                owner_package="bijux-proteomics-lab",
                source_path="packages/bijux-proteomics-lab/src/bijux_proteomics_lab/reconciliation/flagship_follow_up.py",
                test_path="packages/bijux-proteomics-lab/tests/reconciliation/test_reconciliation_flagship_follow_up_surface.py",
                docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
                artifact_paths=(
                    "artifacts/workflows/flagship-workflow-chain/lab/follow_up_packet.json",
                    "artifacts/workflows/flagship-workflow-chain/lab/next_cycle_packet.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-lab/tests/reconciliation/test_reconciliation_flagship_follow_up_surface.py::test_build_flagship_workflow_follow_up_packet_marks_ready_progression",
                ),
            ),
        ),
    )


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(
        f'"{value.replace(chr(34), chr(92) + chr(34))}"' for value in values
    )


def _toml_text(manifest: FlagshipWorkflowManifest) -> str:
    lines = [
        "# Generated flagship workflow manifest.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_runtime.workflows.flagship_workflow_manifest",
        "",
        "[workflow]",
        f'workflow_id = "{manifest.workflow_id}"',
        f'flagship_family_id = "{manifest.flagship_family_id}"',
        f'builder_module = "{manifest.builder_module}"',
        f'builder_symbol = "{manifest.builder_symbol}"',
        f'docs_path = "{manifest.docs_path}"',
        f"owner_packages = [{_render_tuple(manifest.owner_packages)}]",
        f"claim_taxonomy = [{_render_tuple(manifest.claim_taxonomy)}]",
        "",
    ]
    for stage in manifest.stages:
        lines.extend(
            [
                "[[stage]]",
                f'stage = "{stage.stage.value}"',
                f'owner_package = "{stage.owner_package}"',
                f'source_path = "{stage.source_path}"',
                f'test_path = "{stage.test_path}"',
                f'docs_path = "{stage.docs_path}"',
                f"artifact_paths = [{_render_tuple(stage.artifact_paths)}]",
                f"validating_test_ids = [{_render_tuple(stage.validating_test_ids)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(manifest: FlagshipWorkflowManifest) -> bool:
    if not FLAGSHIP_WORKFLOW_MANIFEST_PATH.exists():
        return False
    return FLAGSHIP_WORKFLOW_MANIFEST_PATH.read_text(encoding="utf-8") == _toml_text(
        manifest
    )


def _load_manifest(
    path: Path = FLAGSHIP_WORKFLOW_MANIFEST_PATH,
) -> FlagshipWorkflowManifest:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    workflow = raw["workflow"]
    return FlagshipWorkflowManifest(
        workflow_id=str(workflow["workflow_id"]),
        flagship_family_id=str(workflow["flagship_family_id"]),
        builder_module=str(workflow["builder_module"]),
        builder_symbol=str(workflow["builder_symbol"]),
        docs_path=str(workflow["docs_path"]),
        owner_packages=tuple(str(value) for value in workflow["owner_packages"]),
        claim_taxonomy=tuple(str(value) for value in workflow["claim_taxonomy"]),
        stages=tuple(
            FlagshipWorkflowManifestStageEntry(
                stage=FlagshipWorkflowStage(str(item["stage"])),
                owner_package=str(item["owner_package"]),
                source_path=str(item["source_path"]),
                test_path=str(item["test_path"]),
                docs_path=str(item["docs_path"]),
                artifact_paths=tuple(str(value) for value in item["artifact_paths"]),
                validating_test_ids=tuple(
                    str(value) for value in item["validating_test_ids"]
                ),
            )
            for item in raw["stage"]
        ),
    )


def validate_flagship_workflow_manifest(
    manifest: FlagshipWorkflowManifest | None = None,
    repo_root: Path = REPO_ROOT,
) -> tuple[FlagshipWorkflowManifestIssue, ...]:
    """Validate the checked flagship workflow manifest against live repository truth."""

    manifest = manifest or _load_manifest()
    issues: list[FlagshipWorkflowManifestIssue] = []
    if manifest.workflow_id != "flagship-workflow-chain":
        issues.append(
            FlagshipWorkflowManifestIssue(
                code="unexpected-workflow-id",
                detail=f"flagship workflow manifest must keep workflow_id=flagship-workflow-chain, got {manifest.workflow_id}",
            )
        )
    if set(manifest.claim_taxonomy) != {
        FlagshipWorkflowClaimTier.OWNED_CONTRACT.value,
        FlagshipWorkflowClaimTier.BENCHMARK_BACKED_BEHAVIOR.value,
        FlagshipWorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW.value,
        FlagshipWorkflowClaimTier.FUTURE_WORK.value,
    }:
        issues.append(
            FlagshipWorkflowManifestIssue(
                code="claim-taxonomy-drift",
                detail="flagship workflow manifest no longer carries the governed claim taxonomy",
            )
        )
    if tuple(stage.stage for stage in manifest.stages) != tuple(FlagshipWorkflowStage):
        issues.append(
            FlagshipWorkflowManifestIssue(
                code="stage-set-drift",
                detail="flagship workflow manifest no longer covers the exact stage set",
            )
        )
    for required_owner in manifest.owner_packages:
        if required_owner not in {stage.owner_package for stage in manifest.stages}:
            issues.append(
                FlagshipWorkflowManifestIssue(
                    code="missing-owner-stage",
                    detail=f"flagship workflow manifest no longer covers owner package {required_owner}",
                )
            )
    for stage in manifest.stages:
        for path_label, relative_path in (
            ("source", stage.source_path),
            ("test", stage.test_path),
            ("docs", stage.docs_path),
        ):
            if not (repo_root / relative_path).exists():
                issues.append(
                    FlagshipWorkflowManifestIssue(
                        code=f"missing-{path_label}-path",
                        detail=f"{stage.stage.value} is missing {path_label} path {relative_path}",
                    )
                )
        for artifact_path in stage.artifact_paths:
            if not artifact_path.startswith("artifacts/"):
                issues.append(
                    FlagshipWorkflowManifestIssue(
                        code="artifact-path-outside-artifacts",
                        detail=f"{stage.stage.value} points outside artifacts/: {artifact_path}",
                    )
                )
            if any(token in artifact_path for token in ("simulated", "fake", "_fake")):
                issues.append(
                    FlagshipWorkflowManifestIssue(
                        code="fake-shortcut-artifact-path",
                        detail=f"{stage.stage.value} still references a fake or simulated artifact path: {artifact_path}",
                    )
                )
        for node_id in stage.validating_test_ids:
            if "::" not in node_id:
                issues.append(
                    FlagshipWorkflowManifestIssue(
                        code="invalid-pytest-node-id",
                        detail=f"{stage.stage.value} validating test is not a pytest node id: {node_id}",
                    )
                )
            if any(
                token in node_id for token in ("simulated", "fake", "_fake_run_flow")
            ):
                issues.append(
                    FlagshipWorkflowManifestIssue(
                        code="fake-shortcut-validating-test",
                        detail=f"{stage.stage.value} validating test still depends on a fake-only shortcut: {node_id}",
                    )
                )
    return tuple(issues)


def run(check: bool = False) -> int:
    manifest = build_flagship_workflow_manifest()
    issues = validate_flagship_workflow_manifest(manifest)
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _is_up_to_date(manifest):
            print("flagship workflow manifest is up to date")
            return 0
        print("flagship workflow manifest is stale; regenerate it")
        return 1
    FLAGSHIP_WORKFLOW_MANIFEST_PATH.write_text(_toml_text(manifest), encoding="utf-8")
    print("generated flagship workflow manifest")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the flagship workflow manifest."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the flagship workflow manifest is stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
