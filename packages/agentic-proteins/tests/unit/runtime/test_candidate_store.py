# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.domain.candidates.store import CandidateStore


def _candidate(candidate_id: str) -> Candidate:
    return Candidate(candidate_id=candidate_id, sequence="ACDE")


def test_candidate_store_crud(tmp_path: Path) -> None:
    store = CandidateStore(tmp_path)
    candidate = _candidate("cand-1")
    created = store.create_candidate(candidate)
    assert created.candidate_id == "cand-1"
    fetched = store.get_candidate("cand-1")
    assert fetched.sequence == "ACDE"
    assert store.list_candidates() == ["cand-1"]
    updated = store.update_candidate(
        fetched.model_copy(update={"flags": ["qc_reject"]})
    )
    assert updated.flags == ["qc_reject"]
    store.delete_candidate("cand-1")
    assert store.list_candidates() == []


def test_candidate_versions_and_artifacts(tmp_path: Path) -> None:
    store = CandidateStore(tmp_path)
    candidate = _candidate("cand-2")
    store.create_candidate(candidate)
    versions = store.list_versions("cand-2")
    assert versions
    version_id = versions[0]
    version = store.get_version("cand-2", version_id)
    assert version.version_id == version_id
    record = store.create_artifact("cand-2", version_id, "report", {"ok": True})
    fetched = store.get_artifact("cand-2", version_id, record.artifact_id)
    assert fetched.name == "report"
    assert store.list_artifacts("cand-2", version_id) == [record.artifact_id]


def test_candidate_store_ids_and_validation(tmp_path: Path) -> None:
    store = CandidateStore(tmp_path)
    candidate = _candidate("cand-3")
    assert store.candidate_id_for(candidate.sequence)  # deterministic hash
    assert store.version_id_for(candidate)
    with pytest.raises(ValueError, match="candidate_id required"):
        bad = Candidate.model_construct(candidate_id="", sequence="ACDE")
        store.update_candidate(bad)
    with pytest.raises(ValueError, match="Unsafe candidate_id"):
        store._candidate_path("../bad")
