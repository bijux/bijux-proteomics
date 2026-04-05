# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.domain.candidates.filters import filter_candidates
from agentic_proteins.domain.candidates.model import Candidate


def test_filter_candidates_accepts_valid() -> None:
    candidate = Candidate(candidate_id="c1", sequence="ACD", metrics={"mean_plddt": 80.0})
    assert filter_candidates([candidate]) == [candidate]


def test_filter_candidates_rejects_empty_sequence() -> None:
    candidate = Candidate(candidate_id="c2", sequence="")
    assert filter_candidates([candidate]) == []


def test_filter_candidates_rejects_qc_flag() -> None:
    candidate = Candidate(
        candidate_id="c3",
        sequence="ACD",
        metrics={"mean_plddt": 80.0},
        flags=["qc_reject"],
    )
    assert filter_candidates([candidate]) == []


def test_filter_candidates_rejects_low_plddt() -> None:
    candidate = Candidate(candidate_id="c4", sequence="ACD", metrics={"mean_plddt": 10.0})
    assert filter_candidates([candidate]) == []
