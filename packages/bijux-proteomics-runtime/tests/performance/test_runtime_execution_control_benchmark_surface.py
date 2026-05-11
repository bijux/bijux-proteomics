# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from itertools import count
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_proteomics_runtime.api.catalog import build_artifact_lookup_response
from bijux_proteomics_runtime.runs import RunManager, create_run_context
from bijux_proteomics_runtime.runs.reruns import build_partial_rerun_plan
from bijux_proteomics_runtime.workflows.paths import run_reviewable_sequence_path

from .runtime_benchmark_fixtures import (
    build_medium_rerun_fixture,
    build_medium_startup_config,
    seed_medium_artifact_runs,
)


def _load_execution_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (
                Path(__file__).resolve().parents[1] / "fixtures" / "execution" / name
            ).read_text(encoding="utf-8")
        ),
    )


def _fake_success(candidate, context, tool):  # type: ignore[no-untyped-def]
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.model_dump(),
        "plan_fingerprint": "plan-benchmark",
        "tool_status": "success",
        "report": {
            "status": "ok",
            "observations": [
                {"step": index, "score": round(0.8 + (index % 7) * 0.01, 4)}
                for index in range(96)
            ],
        },
        "qc_status": "acceptable",
        "coordinator_decision": "TerminateRun",
        "failure_type": "none",
        "lifecycle_state": "done",
    }


def test_runtime_startup_benchmark_creates_context_layout_for_medium_config(
    benchmark: Any,
    tmp_path: Path,
) -> None:
    startup_root = tmp_path / "startup"
    startup_root.mkdir(parents=True, exist_ok=True)
    config = build_medium_startup_config()

    context, warnings = benchmark(
        lambda: create_run_context(startup_root, config, run_id=None)
    )

    assert context.workspace.run_dir.exists()
    assert context.config["launch_surface"] == "container"
    assert isinstance(warnings, list)


def test_runtime_artifact_listing_benchmark_scales_across_medium_seeded_runs(
    benchmark: Any,
    tmp_path: Path,
) -> None:
    seed_medium_artifact_runs(tmp_path)

    response = benchmark(
        lambda: build_artifact_lookup_response(
            tmp_path,
            page_size=100,
            max_query_cost=2_000,
        )
    )

    assert response.page.returned_count >= 18


def test_runtime_replay_planning_benchmark_measures_medium_invalidation_cost(
    benchmark: Any,
    tmp_path: Path,
) -> None:
    run_context, expected, current, ledger = build_medium_rerun_fixture(tmp_path)

    plan = benchmark(
        lambda: build_partial_rerun_plan(
            previous_run_context=run_context,
            previous_replay_contract=expected,
            current_replay_contract=current,
            artifact_ledger=ledger,
        )
    )

    assert plan.replay_eligibility.eligible is False
    assert len(plan.replay_eligibility.invalidation_reasons) >= 2


def test_runtime_medium_execution_benchmark_publishes_reviewable_path(
    benchmark: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.run_flow",
        _fake_success,
    )

    manifest = benchmark.pedantic(
        lambda: run_reviewable_sequence_path(tmp_path, sequence="MPEPTIDE"),
        rounds=3,
        iterations=1,
    )

    assert Path(manifest.summary_path).exists()
    assert manifest.command == "run"


def test_runtime_import_benchmark_processes_medium_fixture_payload(
    benchmark: Any,
    tmp_path: Path,
) -> None:
    fixture = _load_execution_fixture("medium_import_benchmark.json")
    source_payload = cast(dict[str, object], fixture["source_payload"])
    source_path = tmp_path / "external" / str(fixture["source_filename"])
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps(source_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    run_ids = count()

    def _import_medium_fixture() -> dict[str, object]:
        run_id = f"runtime-import-medium-{next(run_ids)}"
        return cast(
            dict[str, object],
            RunManager(tmp_path).import_result(
                sequence=str(fixture["sequence"]),
                source_path=source_path,
                imported_payload=dict(source_payload),
                engine_name=str(fixture["engine_name"]),
                engine_version=str(fixture["engine_version"]),
                run_id=run_id,
            ),
        )

    result = benchmark.pedantic(_import_medium_fixture, rounds=3, iterations=1)

    assert result["status"] == "success"
    assert result["report"]["engine_name"] == fixture["engine_name"]
