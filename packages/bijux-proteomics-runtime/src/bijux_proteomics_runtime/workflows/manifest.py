"""Checked manifest for the one workflow family the repository can currently defend."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_runtime.workflows.canonical import (
    CanonicalWorkflowStage,
    WorkflowClaimTier,
    build_flagship_workflow_scope_dossier,
)

__all__ = [
    "CANONICAL_WORKFLOW_MANIFEST_PATH",
    "CanonicalWorkflowManifest",
    "CanonicalWorkflowManifestIssue",
    "CanonicalWorkflowManifestStageEntry",
    "build_canonical_workflow_manifest",
    "run",
    "validate_canonical_workflow_manifest",
]


REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
CANONICAL_WORKFLOW_MANIFEST_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "canonical-workflow-manifest.toml"
)


@dataclass(frozen=True)
class CanonicalWorkflowManifestStageEntry:
    """One owner stage in the checked canonical workflow manifest."""

    stage: CanonicalWorkflowStage
    owner_package: str
    source_path: str
    test_path: str
    docs_path: str
    artifact_paths: tuple[str, ...]
    validating_test_ids: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalWorkflowManifest:
    """Checked manifest for the one canonical workflow family."""

    workflow_id: str
    flagship_family_id: str
    builder_module: str
    builder_symbol: str
    docs_path: str
    owner_packages: tuple[str, ...]
    claim_taxonomy: tuple[str, ...]
    stages: tuple[CanonicalWorkflowManifestStageEntry, ...]


@dataclass(frozen=True)
class CanonicalWorkflowManifestIssue:
    """One manifest issue that blocks canonical workflow truth claims."""

    code: str
    detail: str


def build_canonical_workflow_manifest() -> CanonicalWorkflowManifest:
    """Build the checked manifest for the one canonical workflow family."""

    dossier = build_flagship_workflow_scope_dossier()
    return CanonicalWorkflowManifest(
        workflow_id="canonical-reviewable-proteomics",
        flagship_family_id=dossier.flagship_family_id,
        builder_module="bijux_proteomics_runtime.workflows.canonical",
        builder_symbol="build_canonical_workflow_proof_bundle",
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
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.SEQUENCE_INTAKE,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/sequence-to-digest/targets.fasta",
                    "artifacts/workflows/sequence-to-digest/decoys.fasta",
                    "artifacts/workflows/sequence-to-digest/peptides.tsv",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.SEARCH_AND_CONFIDENCE,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/dda-import/spectra.mgf",
                    "artifacts/workflows/dda-import/psm.tsv",
                    "artifacts/workflows/dda-import/protein_inference.tsv",
                    "artifacts/workflows/dda-import/qc_report.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.QUANTIFICATION,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/quant-runtime/matrix.tsv",
                    "artifacts/workflows/quant-runtime/normalization.json",
                    "artifacts/workflows/quant-runtime/differential_abundance.tsv",
                    "artifacts/workflows/quant-runtime/review_bundle.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.PTM_REVIEW,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/ptm-runtime/ptm_sites.tsv",
                    "artifacts/workflows/ptm-runtime/ptm_occupancy.tsv",
                    "artifacts/workflows/ptm-runtime/ptm_motif_windows.tsv",
                    "artifacts/workflows/ptm-runtime/ptm_lab_packet.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.SCIENTIFIC_KERNEL,
                owner_package="bijux-proteomics-core",
                source_path="packages/bijux-proteomics-core/src/bijux_proteomics/review/canonical_kernel.py",
                test_path="packages/bijux-proteomics-core/tests/review/test_canonical_scientific_kernel_surface.py",
                docs_path="packages/bijux-proteomics-core/README.md",
                artifact_paths=(
                    "artifacts/workflows/canonical-reviewable-proteomics/core/scientific_kernel.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-core/tests/review/test_canonical_scientific_kernel_surface.py::test_build_canonical_scientific_kernel_report_exposes_narrow_scope_boundaries",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.EVIDENCE_REVIEW,
                owner_package="bijux-proteomics-knowledge",
                source_path="packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/reviews/workflow_packets.py",
                test_path="packages/bijux-proteomics-knowledge/tests/reviews/test_workflow_packets_surface.py",
                docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
                artifact_paths=(
                    "artifacts/workflows/canonical-reviewable-proteomics/knowledge/review_packet.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-knowledge/tests/reviews/test_workflow_packets_surface.py::test_build_canonical_evidence_review_packet_preserves_claim_tier_and_artifact_path",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.DECISION_REVIEW,
                owner_package="bijux-proteomics-intelligence",
                source_path="packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/judgment/canonical_reviews.py",
                test_path="packages/bijux-proteomics-intelligence/tests/judgment/test_canonical_reviews_surface.py",
                docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
                artifact_paths=(
                    "artifacts/workflows/canonical-reviewable-proteomics/intelligence/decision_review.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-intelligence/tests/judgment/test_canonical_reviews_surface.py::test_build_flagship_decision_review_allows_lab_when_kernel_and_review_are_clean",
                    "packages/bijux-proteomics-intelligence/tests/judgment/test_canonical_reviews_surface.py::test_build_flagship_decision_review_keeps_downgrade_chain_visible",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.LAB_HANDOFF,
                owner_package="bijux-proteomics-runtime",
                source_path="packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/runs.py",
                test_path="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py",
                docs_path="packages/bijux-proteomics-runtime/README.md",
                artifact_paths=(
                    "artifacts/workflows/lab-handoff/assay_plan.tsv",
                    "artifacts/workflows/lab-handoff/handoff_export.json",
                    "artifacts/workflows/lab-handoff/unresolved_risk_report.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
                ),
            ),
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage.FOLLOW_UP,
                owner_package="bijux-proteomics-lab",
                source_path="packages/bijux-proteomics-lab/src/bijux_proteomics_lab/reconciliation/canonical_follow_up.py",
                test_path="packages/bijux-proteomics-lab/tests/reconciliation/test_canonical_follow_up_surface.py",
                docs_path="docs/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today.md",
                artifact_paths=(
                    "artifacts/workflows/canonical-reviewable-proteomics/lab/follow_up_packet.json",
                    "artifacts/workflows/canonical-reviewable-proteomics/lab/next_cycle_packet.json",
                ),
                validating_test_ids=(
                    "packages/bijux-proteomics-lab/tests/reconciliation/test_canonical_follow_up_surface.py::test_build_canonical_workflow_follow_up_packet_marks_ready_progression",
                ),
            ),
        ),
    )


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value.replace(chr(34), chr(92) + chr(34))}"' for value in values)


def _toml_text(manifest: CanonicalWorkflowManifest) -> str:
    lines = [
        "# Generated canonical workflow manifest.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_runtime.workflows.manifest",
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


def _is_up_to_date(manifest: CanonicalWorkflowManifest) -> bool:
    if not CANONICAL_WORKFLOW_MANIFEST_PATH.exists():
        return False
    return CANONICAL_WORKFLOW_MANIFEST_PATH.read_text(encoding="utf-8") == _toml_text(
        manifest
    )


def _load_manifest(
    path: Path = CANONICAL_WORKFLOW_MANIFEST_PATH,
) -> CanonicalWorkflowManifest:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    workflow = raw["workflow"]
    return CanonicalWorkflowManifest(
        workflow_id=str(workflow["workflow_id"]),
        flagship_family_id=str(workflow["flagship_family_id"]),
        builder_module=str(workflow["builder_module"]),
        builder_symbol=str(workflow["builder_symbol"]),
        docs_path=str(workflow["docs_path"]),
        owner_packages=tuple(str(value) for value in workflow["owner_packages"]),
        claim_taxonomy=tuple(str(value) for value in workflow["claim_taxonomy"]),
        stages=tuple(
            CanonicalWorkflowManifestStageEntry(
                stage=CanonicalWorkflowStage(str(item["stage"])),
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


def validate_canonical_workflow_manifest(
    manifest: CanonicalWorkflowManifest | None = None,
    repo_root: Path = REPO_ROOT,
) -> tuple[CanonicalWorkflowManifestIssue, ...]:
    """Validate the checked canonical workflow manifest against live repository truth."""

    manifest = manifest or _load_manifest()
    issues: list[CanonicalWorkflowManifestIssue] = []
    if manifest.workflow_id != "canonical-reviewable-proteomics":
        issues.append(
            CanonicalWorkflowManifestIssue(
                code="unexpected-workflow-id",
                detail=f"canonical workflow manifest must keep workflow_id=canonical-reviewable-proteomics, got {manifest.workflow_id}",
            )
        )
    if set(manifest.claim_taxonomy) != {
        WorkflowClaimTier.OWNED_CONTRACT.value,
        WorkflowClaimTier.BENCHMARK_BACKED_BEHAVIOR.value,
        WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW.value,
        WorkflowClaimTier.FUTURE_WORK.value,
    }:
        issues.append(
            CanonicalWorkflowManifestIssue(
                code="claim-taxonomy-drift",
                detail="canonical workflow manifest no longer carries the governed claim taxonomy",
            )
        )
    if tuple(stage.stage for stage in manifest.stages) != tuple(CanonicalWorkflowStage):
        issues.append(
            CanonicalWorkflowManifestIssue(
                code="stage-set-drift",
                detail="canonical workflow manifest no longer covers the exact stage set",
            )
        )
    for required_owner in manifest.owner_packages:
        if required_owner not in {stage.owner_package for stage in manifest.stages}:
            issues.append(
                CanonicalWorkflowManifestIssue(
                    code="missing-owner-stage",
                    detail=f"canonical workflow manifest no longer covers owner package {required_owner}",
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
                    CanonicalWorkflowManifestIssue(
                        code=f"missing-{path_label}-path",
                        detail=f"{stage.stage.value} is missing {path_label} path {relative_path}",
                    )
                )
        for artifact_path in stage.artifact_paths:
            if not artifact_path.startswith("artifacts/"):
                issues.append(
                    CanonicalWorkflowManifestIssue(
                        code="artifact-path-outside-artifacts",
                        detail=f"{stage.stage.value} points outside artifacts/: {artifact_path}",
                    )
                )
            if any(token in artifact_path for token in ("simulated", "fake", "_fake")):
                issues.append(
                    CanonicalWorkflowManifestIssue(
                        code="fake-shortcut-artifact-path",
                        detail=f"{stage.stage.value} still references a fake or simulated artifact path: {artifact_path}",
                    )
                )
        for node_id in stage.validating_test_ids:
            if "::" not in node_id:
                issues.append(
                    CanonicalWorkflowManifestIssue(
                        code="invalid-pytest-node-id",
                        detail=f"{stage.stage.value} validating test is not a pytest node id: {node_id}",
                    )
                )
            if any(token in node_id for token in ("simulated", "fake", "_fake_run_flow")):
                issues.append(
                    CanonicalWorkflowManifestIssue(
                        code="fake-shortcut-validating-test",
                        detail=f"{stage.stage.value} validating test still depends on a fake-only shortcut: {node_id}",
                    )
                )
    return tuple(issues)


def run(check: bool = False) -> int:
    manifest = build_canonical_workflow_manifest()
    issues = validate_canonical_workflow_manifest(manifest)
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _is_up_to_date(manifest):
            print("canonical workflow manifest is up to date")
            return 0
        print("canonical workflow manifest is stale; regenerate it")
        return 1
    CANONICAL_WORKFLOW_MANIFEST_PATH.write_text(_toml_text(manifest), encoding="utf-8")
    print("generated canonical workflow manifest")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the canonical workflow manifest."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the canonical workflow manifest is stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
