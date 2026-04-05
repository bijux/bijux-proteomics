# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from agentic_proteins.domain.structure.structure import kabsch_and_pairs, tm_score
from agentic_proteins.core.fingerprints import hash_payload
from agentic_proteins.providers.factory import (
    PROVIDER_CAPABILITIES,
    cuda_available,
    provider_requirements,
)
from tests.helpers.artifacts import assert_valid_run_artifacts

REAL_CASES = [
    {
        "name": "ubiquitin_chainA",
        "fasta": "examples/ex02_1ubq_A/seq_1ubq_chainA.fasta",
        "ground_truth": "examples/ex02_1ubq_A/ground_truth_1ubq_A.pdb",
    },
    {
        "name": "crambin_chainA",
        "fasta": "examples/ex03_1crn_A/seq_1crn_chainA.fasta",
        "ground_truth": "examples/ex03_1crn_A/ground_truth_1crn_A.pdb",
    },
]

LOCAL_PROVIDERS = [
    "local_esmfold",
    pytest.param("local_rosettafold", marks=pytest.mark.gpu),
]


def _run_cli(
    root: Path,
    outdir: Path,
    *,
    provider: str,
    fasta: Path,
    execution_mode: str,
) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "agentic_proteins.interfaces.cli",
        "run",
        "--json",
        "--provider",
        provider,
        "--fasta",
        str(fasta),
        "--artifacts-dir",
        str(outdir),
        "--execution-mode",
        execution_mode,
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    (outdir / "stdout.txt").write_text(proc.stdout)
    (outdir / "stderr.txt").write_text(proc.stderr)
    assert proc.returncode == 0, f"CLI failed.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    return json.loads(proc.stdout)


@pytest.mark.real
@pytest.mark.real_local
@pytest.mark.timeout(0)
@pytest.mark.parametrize("case", REAL_CASES)
@pytest.mark.parametrize("provider", LOCAL_PROVIDERS)
def test_real_local_prediction(
    ROOT: Path, run_output_dir: callable, case: dict, provider: str
) -> None:
    """Run real local models and assert artifacts/metrics are produced."""
    capabilities = PROVIDER_CAPABILITIES.get(provider)
    if capabilities and capabilities.supports_gpu and not capabilities.supports_cpu:
        if not cuda_available():
            pytest.skip("GPU required for this provider")
        execution_mode = "gpu"
    else:
        execution_mode = "cpu"
    errors = provider_requirements(provider)
    assert not errors, f"Provider requirements unmet for {provider}: {errors}"

    outdir = run_output_dir(case["name"], provider)
    fasta = ROOT / case["fasta"]
    ground_truth = ROOT / case["ground_truth"]
    assert fasta.exists(), f"Missing FASTA: {fasta}"
    assert ground_truth.exists(), f"Missing ground truth: {ground_truth}"

    payload = _run_cli(
        ROOT, outdir, provider=provider, fasta=fasta, execution_mode=execution_mode
    )
    run_id = payload["run_id"]
    run_dir = outdir / run_id
    artifacts_payload = assert_valid_run_artifacts(run_dir)

    predicted_pdb = run_dir / "predicted.pdb"
    report_json = run_dir / "report.json"

    assert predicted_pdb.exists(), "No predicted.pdb produced"
    assert predicted_pdb.stat().st_size > 500, "Predicted PDB is suspiciously small"
    assert report_json.exists(), "No report.json produced"

    report = artifacts_payload["report"] or {}
    outputs = report.get("summary", {}).get("outputs", {})
    assert "mean_plddt" in outputs, "mean_plddt missing from report outputs"

    pred_text = predicted_pdb.read_text()
    ref_text = ground_truth.read_text()
    rmsd, _pairs, ref_coords, pred_coords, _seq_id, _gap = kabsch_and_pairs(
        pred_text, ref_text
    )
    tm = tm_score(ref_coords, pred_coords)

    assert rmsd >= 0.0, "RMSD must be non-negative"
    assert tm > 0.0, "TM-score must be positive"


@pytest.mark.real_local
@pytest.mark.slow
@pytest.mark.timeout(0)
def test_cpu_fallback_small_protein(ROOT: Path, run_output_dir: callable) -> None:
    """Run a small protein on CPU and verify fallback warning + runtime bound."""
    if not PROVIDER_CAPABILITIES["local_esmfold"].supports_cpu:
        pytest.skip("CPU fallback not supported for local_esmfold")
    fasta = ROOT / "examples/ex03_1crn_A/seq_1crn_chainA.fasta"
    assert fasta.exists(), f"Missing FASTA: {fasta}"

    outdir = run_output_dir("cpu_fallback_small", "local_esmfold")
    start = time.monotonic()
    payload = _run_cli(
        ROOT, outdir, provider="local_esmfold", fasta=fasta, execution_mode="cpu"
    )
    duration = time.monotonic() - start
    assert duration < 900, f"CPU fallback exceeded time budget: {duration:.1f}s"

    run_id = payload["run_id"]
    run_dir = outdir / run_id
    artifacts_payload = assert_valid_run_artifacts(run_dir)
    run_output = artifacts_payload["run_output"]
    report_payload = artifacts_payload["report"] or {}
    outputs = report_payload.get("summary", {}).get("outputs", {})
    assert "mean_plddt" in outputs, "mean_plddt missing from report outputs"
    warnings = run_output.get("warnings", [])
    assert any(
        w.startswith("cpu_mode:local_esmfold") or w.startswith("cpu_fallback:local_esmfold")
        for w in warnings
    ), "CPU fallback warning not recorded"


@pytest.mark.real_local
@pytest.mark.timeout(0)
def test_artifact_contract_local_esmfold(
    ROOT: Path, run_output_dir: callable
) -> None:
    """Verify report schema + hash stability + artifact presence."""
    fasta = ROOT / "examples/ex02_1ubq_A/seq_1ubq_chainA.fasta"
    assert fasta.exists(), f"Missing FASTA: {fasta}"

    outdir = run_output_dir("artifact_contract", "local_esmfold")
    payload = _run_cli(
        ROOT, outdir, provider="local_esmfold", fasta=fasta, execution_mode="cpu"
    )
    run_id = payload["run_id"]
    run_dir = outdir / run_id

    predicted_pdb = run_dir / "predicted.pdb"
    report_json = run_dir / "report.json"
    assert predicted_pdb.exists(), "Missing predicted.pdb"
    assert report_json.exists(), "Missing report.json"

    report_payload = json.loads(report_json.read_text())
    summary = report_payload.get("summary", {})
    outputs = summary.get("outputs", {})
    assert summary, "Report summary missing"
    assert outputs, "Report outputs missing"
    assert "mean_plddt" in outputs, "mean_plddt missing from report outputs"

    hash_a = hash_payload(report_payload)
    reencoded = json.loads(json.dumps(report_payload, sort_keys=True, separators=(",", ":")))
    hash_b = hash_payload(reencoded)
    assert hash_a == hash_b, "Report hash is not stable across serialization"


@pytest.mark.real_local
@pytest.mark.gpu
@pytest.mark.timeout(0)
def test_missing_weights_fail_cleanly(
    ROOT: Path, run_output_dir: callable
) -> None:
    """Ensure missing weights fail cleanly without partial artifacts."""
    if not cuda_available():
        pytest.skip("GPU required for local_rosettafold")
    weights_path = ROOT / "models/rosettafold/RFAA_paper_weights.pt"
    backup_path = weights_path.with_suffix(".pt.bak")
    had_weights = weights_path.exists()
    if had_weights:
        weights_path.replace(backup_path)
    try:
        fasta = ROOT / "examples/ex02_1ubq_A/seq_1ubq_chainA.fasta"
        outdir = run_output_dir("missing_weights", "local_rosettafold")
        payload = _run_cli(
            ROOT,
            outdir,
            provider="local_rosettafold",
            fasta=fasta,
            execution_mode="gpu",
        )
        run_id = payload["run_id"]
        run_dir = outdir / run_id

        error_path = run_dir / "error.json"
        report_path = run_dir / "report.json"
        predicted_pdb = run_dir / "predicted.pdb"
        telemetry_path = run_dir / "telemetry.json"

        assert payload["execution_status"] == "errored"
        assert payload["failure"] == "capability_missing"
        assert error_path.exists(), "Missing error.json"
        assert not report_path.exists(), "Report should not be written on failure"
        assert not predicted_pdb.exists(), "Predicted PDB should not exist on failure"

        error_payload = json.loads(error_path.read_text())
        assert "missing_weights" in error_payload.get("message", "")
        telemetry = json.loads(telemetry_path.read_text())
        assert "run_start" in telemetry.get("events", [])
    finally:
        if backup_path.exists():
            backup_path.replace(weights_path)
