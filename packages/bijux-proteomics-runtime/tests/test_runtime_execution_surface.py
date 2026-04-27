from __future__ import annotations

import importlib.metadata

import pytest

from bijux_proteomics_runtime.core.hashing import sha256_hex
from bijux_proteomics_runtime.runtime.control.artifacts import _sign_payload
from bijux_proteomics_runtime.runtime.control.execution import _version_info
from bijux_proteomics_runtime.runtime.control.state_machine import RunStateMachine


def test_runtime_replay_hash_contract() -> None:
    assert len(sha256_hex("runtime")) == 64


def test_runtime_state_machine_constructs() -> None:
    machine = RunStateMachine()
    assert machine is not None


def test_runtime_artifact_surface_exports_signature_helper() -> None:
    assert _sign_payload is not None


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
