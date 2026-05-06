from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_runtime.runs.cache import (
    claim_runtime_cache,
    release_runtime_cache_claim,
)
from bijux_proteomics_runtime.runs.context import create_run_context
from bijux_proteomics_runtime.runs.contracts import (
    RuntimeArtifactRetentionClass,
    build_run_context_contract,
)
from bijux_proteomics_runtime.runs.integrity import (
    load_artifact_integrity_report,
    verify_runtime_artifact_integrity,
)
from bijux_proteomics_runtime.runs.ledger import (
    ArtifactLedgerEntry,
    RuntimeArtifactLedger,
)
from bijux_proteomics_runtime.runs.manager import RunManager
from bijux_proteomics_runtime.runs.replay import (
    build_replay_contract,
    load_local_run_bundle,
)
from bijux_proteomics_runtime.runs.reruns import build_partial_rerun_plan
from bijux_proteomics_runtime.support.workspace import RunWorkspace

from ..support.fixture_data import load_fixture


def _build_contract(
    tmp_path: Path,
    *,
    run_id: str,
    sequence: str,
    provider_name: str,
) -> tuple[object, object]:
    context, _ = create_run_context(tmp_path, run_id=run_id)
    run_context = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name=provider_name,
        artifact_policy=context.artifact_policy,
        sequence=sequence,
        command="run",
        workflow_family="sequence_to_digest",
        candidate_id=f"{run_id}-c0",
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={provider_name: "0.1"},
    )
    return run_context, replay_contract


def _ledger(run_id: str, artifact_kinds: list[str]) -> RuntimeArtifactLedger:
    return RuntimeArtifactLedger(
        run_id=run_id,
        entries=tuple(
            ArtifactLedgerEntry(
                artifact_role=f"role-{index}",
                artifact_kind=artifact_kind,
                path=f"/tmp/{run_id}/{artifact_kind}.json",
                producer="fixture",
                retention_class=RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
                content_sha256="0" * 64,
                size_bytes=32,
            )
            for index, artifact_kind in enumerate(artifact_kinds)
        ),
    )


def test_runtime_replay_fixture_proves_reuse_refusal_and_partial_rerun(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "replay_rerun_path.json")
    previous_context, previous_contract = _build_contract(
        tmp_path,
        run_id=str(fixture["run_id"]),
        sequence=str(fixture["sequence"]),
        provider_name=str(fixture["exact_reuse"]["provider_name"]),
    )
    _same_context, current_exact = _build_contract(
        tmp_path,
        run_id=str(fixture["run_id"]),
        sequence=str(fixture["sequence"]),
        provider_name=str(fixture["exact_reuse"]["provider_name"]),
    )
    _changed_context, current_partial = _build_contract(
        tmp_path,
        run_id=str(fixture["run_id"]),
        sequence=str(fixture["sequence"]),
        provider_name=str(fixture["partial_rerun"]["provider_name"]),
    )
    _input_context, current_full = _build_contract(
        tmp_path,
        run_id=str(fixture["run_id"]),
        sequence=str(fixture["full_rerun"]["sequence"]),
        provider_name=str(fixture["exact_reuse"]["provider_name"]),
    )
    ledger = _ledger(str(fixture["run_id"]), list(fixture["artifact_kinds"]))

    exact_plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=current_exact,
        artifact_ledger=ledger,
    )
    partial_plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=current_partial,
        artifact_ledger=ledger,
    )
    full_plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=current_full,
        artifact_ledger=ledger,
    )

    assert exact_plan.replay_eligibility.eligible is True
    assert [step.node_id for step in exact_plan.reuse_steps] == fixture["exact_reuse"][
        "expected_reuse_steps"
    ]
    assert [step.node_id for step in exact_plan.rerun_steps] == fixture["exact_reuse"][
        "expected_rerun_steps"
    ]

    assert partial_plan.replay_eligibility.eligible is False
    assert (
        list(partial_plan.replay_eligibility.invalidation_reasons)
        == fixture["partial_rerun"]["expected_invalidation_reasons"]
    )
    assert [step.node_id for step in partial_plan.reuse_steps] == fixture[
        "partial_rerun"
    ]["expected_reuse_steps"]
    assert [step.node_id for step in partial_plan.rerun_steps] == fixture[
        "partial_rerun"
    ]["expected_rerun_steps"]

    assert full_plan.replay_eligibility.eligible is False
    assert (
        list(full_plan.replay_eligibility.invalidation_reasons)
        == fixture["full_rerun"]["expected_invalidation_reasons"]
    )
    assert [step.node_id for step in full_plan.reuse_steps] == fixture["full_rerun"][
        "expected_reuse_steps"
    ]
    assert [step.node_id for step in full_plan.rerun_steps] == fixture["full_rerun"][
        "expected_rerun_steps"
    ]


def test_runtime_corruption_fixture_refuses_reuse_of_modified_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_fixture("execution", "sequence_review_path.json")

    def _fake_run_flow(candidate, context, tool):  # type: ignore[no-untyped-def]
        result = dict(fixture["fake_run_flow_result"])
        result["candidate_id"] = candidate.candidate_id
        result["candidate"] = candidate.model_dump()
        return result

    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.run_flow",
        _fake_run_flow,
    )

    run_id = "runtime-corruption-proof-1"
    manager = RunManager(tmp_path)
    manager.run(str(fixture["sequence"]), run_id=run_id)
    workspace = RunWorkspace.for_run(tmp_path, run_id)
    workspace.local_run_bundle_path.write_text('{"corrupted": true}', encoding="utf-8")

    report = verify_runtime_artifact_integrity(
        workspace,
        run_id=run_id,
        max_artifact_bytes=1_000_000,
    )
    reloaded = load_artifact_integrity_report(workspace)

    assert report.verified is False
    assert reloaded.verified is False
    assert any(issue.issue_code == "artifact_corrupted" for issue in report.issues)
    with pytest.raises(ValueError, match="artifact_corrupted"):
        load_local_run_bundle(workspace)


def test_runtime_cache_fixture_refuses_unsafe_reuse_until_holder_releases(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "cache_claim_safety.json")
    cache_root = tmp_path / "artifacts" / "cache"
    cache_key = str(fixture["cache_key"])

    decisions = [
        claim_runtime_cache(
            cache_root,
            cache_key=cache_key,
            run_id=str(claim["run_id"]),
            access_mode=str(claim["access_mode"]),
            input_fingerprint=str(claim["input_fingerprint"]),
        )
        for claim in fixture["claims"]
    ]

    for decision, claim in zip(decisions, fixture["claims"], strict=True):
        assert decision.allowed is claim["expected_allowed"]
        assert decision.holder_run_id == claim["expected_holder_run_id"]

    release_runtime_cache_claim(cache_root, cache_key=cache_key, run_id="review-a")
    resumed = claim_runtime_cache(
        cache_root,
        cache_key=cache_key,
        run_id="review-c",
        access_mode="exclusive_write",
        input_fingerprint="dia-library:v2",
    )

    assert resumed.allowed is True
    assert resumed.holder_run_id == "review-c"
