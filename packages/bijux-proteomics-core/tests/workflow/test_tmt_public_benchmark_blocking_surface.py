# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from bijux_proteomics.workflow import (
    PublicBenchmarkFailureKind,
    public_benchmark_root,
    run_public_benchmark_descriptor,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_descriptor_copy(
    tmp_path: Path,
    *,
    source_name: str,
    design_path: Path,
) -> Path:
    source_path = public_benchmark_root() / source_name / "dataset.yml"
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    for source in payload["source_files"]:
        if source["schema_id"] == "design_tsv":
            source["repo_relative_path"] = str(design_path)
            source["sha256"] = _sha256(design_path)
            break
    target_dir = tmp_path / source_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "dataset.yml"
    target_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return target_path


def test_public_benchmark_runner_blocks_tmt_descriptor_with_duplicate_channel_mapping(
    tmp_path: Path,
) -> None:
    duplicate_design = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "multiplex"
        / "tmt_duplicate_channel.design.tsv"
    )
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        source_name="multiplex_tmtpro_review_package",
        design_path=duplicate_design,
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.MULTIPLEX_CHANNEL_MAPPING_INVALID
        and failure.subject == "duplicate_channel_assignment"
        for failure in report.failures
    )
