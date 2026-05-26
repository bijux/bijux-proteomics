"""Tests for the curated architecture regression gate contract."""

from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.quality.gates.architecture_regression_gate import (
    default_architecture_regression_targets,
    run_canonical_internal_architecture_map,
    run_canonical_root_imports,
    run_architecture_regression_gate,
    validate_architecture_regression_targets,
)


def test_architecture_regression_gate_targets_cover_expected_surfaces() -> None:
    targets = default_architecture_regression_targets()

    assert {target.surface for target in targets} == {
        "canonical-root-imports",
        "public-api-snapshots",
        "internal-architecture-map",
        "canonical-package-tree",
        "runtime-architecture-demo",
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
    assert commands[0][1:3] == ("-m", "bijux_proteomics_dev.quality.gates.architecture_regression_gate")
    assert commands[1][1:3] == ("-m", "bijux_proteomics_dev.governance.package_shape.public_api_snapshots")


def test_canonical_root_imports_check_only_canonical_product_packages(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    commands: list[tuple[str, ...]] = []

    def fake_run_subprocess(command: tuple[str, ...], *, cwd: Path) -> tuple[bool, str]:
        assert cwd == tmp_path
        commands.append(command)
        return True, "ok"

    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate._run_subprocess",
        fake_run_subprocess,
    )

    assert run_canonical_root_imports(tmp_path, python_executable="/python") == 0
    assert len(commands) == 6
    assert commands[0] == ("/python", "-c", "import bijux_proteomics_foundation")
    assert commands[-1] == ("/python", "-c", "import bijux_proteomics_runtime")


def test_canonical_internal_architecture_map_accepts_explicit_no_cycle_override(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate.build_internal_architecture_map_report",
        lambda: object(),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate.evaluate_internal_architecture_violations",
        lambda report, workspace_cycles=(): (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.quality.gates.architecture_regression_gate.is_internal_architecture_map_up_to_date",
        lambda report: True,
    )

    assert run_canonical_internal_architecture_map() == 0
