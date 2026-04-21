from __future__ import annotations

from bijux_proteomics_runtime.core.hashing import sha256_hex
from bijux_proteomics_runtime.runtime.control.state_machine import RunStateMachine


def test_runtime_replay_hash_contract() -> None:
    assert len(sha256_hex("runtime")) == 64


def test_runtime_state_machine_constructs() -> None:
    machine = RunStateMachine()
    assert machine is not None
