# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Hard biological constraints for candidate filtering."""

from __future__ import annotations

from agentic_proteins.domain.candidates.model import Candidate


def filter_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """filter_candidates."""
    filtered: list[Candidate] = []
    for candidate in candidates:
        if _fails_hard_constraints(candidate):
            continue
        filtered.append(candidate)
    return filtered


def _fails_hard_constraints(candidate: Candidate) -> bool:
    """_fails_hard_constraints."""
    if not candidate.sequence:
        return True
    if "qc_reject" in candidate.flags:
        return True
    mean_plddt = float(candidate.metrics.get("mean_plddt", 0.0))
    return mean_plddt < 50.0
