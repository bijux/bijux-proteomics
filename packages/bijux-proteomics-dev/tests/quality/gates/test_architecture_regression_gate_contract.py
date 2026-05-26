"""Tests for the curated architecture regression gate contract."""

from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.quality.gates.architecture_regression_gate import (
    default_architecture_regression_targets,
    run_architecture_regression_gate,
    validate_architecture_regression_targets,
)


def test_architecture_regression_gate_targets_cover_expected_surfaces() -> None:
    targets = default_architecture_regression_targets()

    assert {target.surface for target in targets} == {
        "imports-and-collection",
        "public-api-snapshots",
        "internal-architecture-map",
        "canonical-package-tree",
        "runtime-output-snapshots",
        "workflow-output-validation",
        "shipped-demo-cli",
    }


def test_architecture_regression_gate_targets_exist() -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )

    assert validate_architecture_regression_targets(repo_root) == []
    assert run_architecture_regression_gate(repo_root, execute=False) == 0


def test_architecture_regression_gate_executes_every_target(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    commands: list[tuple[str, ...]] = []
    sample_targets = default_architecture_regression_targets()[:2]

    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate.default_architecture_regression_targets",
        lambda: sample_targets,
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate.validate_architecture_regression_targets",
        lambda repo_root: [],
    )

    def fake_run_subprocess(command: tuple[str, ...], *, cwd: Path) -> tuple[bool, str]:
        assert cwd == tmp_path
        commands.append(command)
        return True, "ok"

    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate._run_subprocess",
        fake_run_subprocess,
    )

    assert run_architecture_regression_gate(tmp_path, execute=True) == 0
    assert len(commands) == 2
    assert commands[0][1:3] == ("-m", "bijux_proteomics_dev.release.governance.test_collection_gate")
    assert commands[1][1:3] == ("-m", "bijux_proteomics_dev.governance.package_shape.public_api_snapshots")
