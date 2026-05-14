# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows.paths import run_reviewable_sequence_path


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "first_useful_run" / name


def _first_sequence_from_fixture() -> str:
    lines = _fixture("proteins.fasta").read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line and not line.startswith(">"))


def test_runtime_operator_path_executes_real_sequence_review_bundle(
    tmp_path: Path,
) -> None:
    manifest = run_reviewable_sequence_path(
        tmp_path,
        sequence=_first_sequence_from_fixture(),
        execution_mode="cpu",
    )

    assert manifest.command == "run"
    assert manifest.workflow_family == "sequence_to_digest"
    assert manifest.import_only is False
    assert set(manifest.artifact_kinds) == {
        "runtime-status",
        "runtime-report",
        "runtime-replay-contract",
        "runtime-integrity-report",
    }
    assert Path(manifest.summary_path).exists()
    assert Path(manifest.report_path).exists()
    assert Path(manifest.replay_contract_path).exists()
    assert Path(manifest.integrity_report_path).exists()
