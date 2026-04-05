# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_proteins.domain.candidates import CandidateStore


def test_abuse_case_path_traversal_blocked(tmp_path) -> None:
    store = CandidateStore(tmp_path / "candidate_store")
    with pytest.raises(ValueError):
        store.get_candidate("../secrets")
