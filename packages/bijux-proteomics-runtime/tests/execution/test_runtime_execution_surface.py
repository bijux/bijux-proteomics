from __future__ import annotations

import importlib.metadata

import pytest

from bijux_proteomics_foundation import hash_text
from bijux_proteomics_runtime.support.primitives.hashing import sha256_hex
from bijux_proteomics_runtime.runs.artifacts import _sign_payload
from bijux_proteomics_runtime.runs.manager import (
    _build_run_summary,
    _ensure_telemetry_costs,
    _select_structure_tool,
    _version_info,
)
from bijux_proteomics_runtime.runs.state_machine import RunStateMachine


def test_runtime_replay_hash_contract() -> None:
    assert len(sha256_hex("runtime")) == 64
    assert sha256_hex("runtime") == hash_text("runtime")


def test_runtime_state_machine_constructs() -> None:
    machine = RunStateMachine()
    assert machine is not None


def test_runtime_artifact_surface_exports_signature_helper() -> None:
    assert _sign_payload is not None


def test_runtime_execution_surface_exports_summary_helpers() -> None:
    assert _build_run_summary is not None
    assert _version_info is not None


def test_runtime_execution_surface_exports_runtime_support_helpers() -> None:
    assert _select_structure_tool is not None
    assert _ensure_telemetry_costs is not None


def test_runtime_version_info_queries_canonical_distribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: list[str] = []

    def _version(name: str) -> str:
        requested.append(name)
        return "1.2.3"

    monkeypatch.setattr(importlib.metadata, "version", _version)

    info = _version_info(None)

    assert requested == ["bijux-proteomics-runtime"]
    assert info.app_version == "1.2.3"
