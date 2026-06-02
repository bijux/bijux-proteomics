"""Tests for repository API freeze contract checks."""

from __future__ import annotations

from pathlib import Path

from pytest import CaptureFixture
from pytest import MonkeyPatch

import bijux_proteomics_dev.governance.contracts.freeze_contracts as freeze_contracts_module
from bijux_proteomics_dev.governance.contracts.freeze_contracts import (
    run as run_api_freeze_contracts,
)


def test_api_freeze_contracts_pass_for_repository() -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )
    assert run_api_freeze_contracts(repo_root) == 0


def test_api_freeze_contracts_report_shared_function_signature_drift(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )
    monkeypatch.setattr(
        freeze_contracts_module,
        "validate_cross_package_function_signatures",
        lambda: (
            "signature drift for bijux_proteomics.dia.build_dia_capability_matrix: old -> new",
        ),
    )

    assert run_api_freeze_contracts(repo_root) == 1

    stderr = capsys.readouterr().err
    assert "API freeze contract violations detected:" in stderr
    assert (
        "- signature drift for bijux_proteomics.dia.build_dia_capability_matrix: old -> new"
        in stderr
    )
