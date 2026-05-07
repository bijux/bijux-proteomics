# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.workflows import (
    build_flagship_cross_family_run_bundle,
    build_flagship_run_bundle,
    build_flagship_run_bundle_family,
    build_flagship_run_failure_replay,
    build_flagship_run_registry,
    build_flagship_run_stage_lineage,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
FIXTURE_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-runtime"
    / "tests"
    / "fixtures"
    / "flagship_runs"
)


def _read_fixture(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_flagship_run_bundle_family_covers_all_six_flagship_workflows(
    tmp_path: Path,
) -> None:
    bundles = build_flagship_run_bundle_family(base_dir=tmp_path)

    assert tuple(bundle.workflow_family for bundle in bundles) == (
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    )


def test_flagship_run_bundles_keep_runtime_and_downstream_artifacts_linked(
    tmp_path: Path,
) -> None:
    dda = build_flagship_run_bundle("dda", base_dir=tmp_path / "dda")
    lfq = build_flagship_run_bundle("lfq", base_dir=tmp_path / "lfq")
    targeted = build_flagship_run_bundle("targeted", base_dir=tmp_path / "targeted")

    assert dda.runtime_surface.run_mode.value == "import_only"
    assert dda.runtime_surface.proof_class.value == "import_backed_execution"
    assert any(
        artifact.artifact_role == "runtime-imported-evidence"
        for artifact in dda.artifact_inventory
    )
    assert any(
        path.endswith("recommendation-packets/dda.json")
        for path in dda.linked_owner_artifact_paths
    )

    assert lfq.runtime_surface.run_mode.value == "raw_executable"
    assert lfq.runtime_surface.proof_class.value == "raw_execution"
    assert any(
        "review_bundle_hash=" in line for line in lfq.runtime_surface.execution_summary
    )
    assert any(
        artifact.artifact_role == "runtime-output" for artifact in lfq.artifact_inventory
    )

    assert targeted.runtime_surface.toolchain_or_import_path == (
        "targeted transition review corpus"
    )
    assert any(
        "release-facing trust remains narrower than runtime execution"
        in blocker
        for blocker in targeted.remaining_blockers
    )


def test_cross_family_bundle_and_registry_publish_runtime_review_surfaces(
    tmp_path: Path,
) -> None:
    cross_family = build_flagship_cross_family_run_bundle(base_dir=tmp_path)
    registry = build_flagship_run_registry(base_dir=tmp_path)

    assert cross_family.workflow_families == (
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    )
    assert len(cross_family.per_family_bundle_paths) == 6
    assert any(
        path.endswith("scientific-reading-packs/dda.json")
        for path in cross_family.knowledge_artifact_paths
    )
    assert len(registry.entries) == 6
    assert registry.entries[0].bundle_artifact_path.endswith("dda/run_bundle.json")
    assert registry.entries[0].proof_class.value == "import_backed_execution"
    assert any(
        entry.runtime_package_id == "targeted-transition-review-corpus"
        for entry in registry.entries
    )


def test_checked_flagship_run_snapshots_match_runtime_builders(tmp_path: Path) -> None:
    bundles = {
        bundle.workflow_family: bundle
        for bundle in build_flagship_run_bundle_family(base_dir=tmp_path)
    }
    for workflow_family, bundle in bundles.items():
        assert _read_fixture(FIXTURE_ROOT / workflow_family / "run_bundle.json") == bundle.to_dict()
        assert _read_fixture(FIXTURE_ROOT / workflow_family / "stage_lineage.json") == (
            build_flagship_run_stage_lineage(workflow_family).to_dict()
        )
        assert _read_fixture(FIXTURE_ROOT / workflow_family / "failure_replay.json") == (
            build_flagship_run_failure_replay(workflow_family, base_dir=tmp_path / f"{workflow_family}-failure").to_dict()
        )

    cross_family = build_flagship_cross_family_run_bundle(base_dir=tmp_path)
    registry = build_flagship_run_registry(base_dir=tmp_path)

    assert _read_fixture(FIXTURE_ROOT / "cross_family_run_bundle.json") == cross_family.to_dict()
    assert _read_fixture(FIXTURE_ROOT / "runtime_run_registry.json") == registry.to_dict()
