# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows.flagship_workflow_chain import FlagshipWorkflowStage
from bijux_proteomics_runtime.workflows.flagship_workflow_manifest import (
    FLAGSHIP_WORKFLOW_MANIFEST_PATH,
    build_flagship_workflow_manifest,
    run,
    validate_flagship_workflow_manifest,
)

from .test_flagship_workflow_chain_surface import _build_bundle

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_flagship_workflow_manifest_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_flagship_workflow_manifest_matches_checked_bundle_shape() -> None:
    manifest = build_flagship_workflow_manifest()
    bundle = _build_bundle()

    manifest_stage_map = {entry.stage: entry for entry in manifest.stages}
    bundle_stage_map = {stage.stage: stage for stage in bundle.stages}

    assert FLAGSHIP_WORKFLOW_MANIFEST_PATH.exists()
    assert tuple(manifest_stage_map) == tuple(FlagshipWorkflowStage)
    assert set(manifest.owner_packages) == {
        "bijux-proteomics-runtime",
        "bijux-proteomics-core",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }
    for stage in FlagshipWorkflowStage:
        assert manifest_stage_map[stage].owner_package == bundle_stage_map[stage].owner_package
        assert manifest_stage_map[stage].artifact_paths == bundle_stage_map[stage].artifact_paths


def test_flagship_workflow_manifest_refuses_fake_only_shortcuts() -> None:
    issues = validate_flagship_workflow_manifest(repo_root=REPO_ROOT)

    assert issues == ()
