# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.support.provenance import (
    ProvenancePointer,
    ProvenancePointerKind,
)
from bijux_proteomics_foundation.support.states import SupportState


def test_provenance_pointer_orders_labels_and_keeps_alias_contracts() -> None:
    pointer = ProvenancePointer(
        pointer_kind=ProvenancePointerKind.DOCUMENT,
        locator="documents/review/report.json",
        pointer_role="review_artifact",
        pointer_labels=("zeta", "alpha", "beta"),
    )

    rendered = pointer.to_dict()

    assert rendered["pointer_role"] == "review_artifact"
    assert rendered["pointer_labels"] == ["alpha", "beta", "zeta"]


def test_support_state_surface_stays_within_curated_kernel_vocabulary() -> None:
    assert tuple(SupportState) == (
        SupportState.ADVISORY,
        SupportState.SUPPORTED,
        SupportState.REFUSED,
        SupportState.AMBIGUOUS,
        SupportState.INCOMPLETE,
        SupportState.LOSSY,
    )
