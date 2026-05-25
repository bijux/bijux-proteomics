# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import string

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, ValidationError

from bijux_proteomics_foundation.identity.identifiers import (
    IdentifierKind,
    LabActionId,
    PtmId,
    ReviewPacketId,
    StudyId,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
)

IDENTIFIER_SUFFIX_STRATEGY = st.lists(
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=8),
    min_size=1,
    max_size=4,
)
IDENTIFIER_RAW_SUFFIX_STRATEGY = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=24,
).filter(lambda value: bool(value.strip()))


class IdentifierSurface(BaseModel):
    study_id: StudyId
    ptm_id: PtmId
    review_packet_id: ReviewPacketId
    lab_action_id: LabActionId


def test_identifier_surface_covers_foundation_owned_scientific_entities() -> None:
    surface = IdentifierSurface(
        study_id=build_identifier(IdentifierKind.STUDY, "Study-01"),
        ptm_id=build_identifier(IdentifierKind.PTM, "Phospho-S123"),
        review_packet_id=build_identifier(IdentifierKind.REVIEW_PACKET, "Panel-A"),
        lab_action_id=build_identifier(IdentifierKind.LAB_ACTION, "Queue-Transfer"),
    )

    assert surface.study_id == "study-study-01"
    assert surface.ptm_id == "ptm-phospho-s123"
    assert surface.review_packet_id == "reviewpkt-panel-a"
    assert surface.lab_action_id == "labact-queue-transfer"

    with pytest.raises(ValidationError):
        IdentifierSurface(
            study_id="bad id",
            ptm_id="ptm-ok",
            review_packet_id="reviewpkt-ok",
            lab_action_id="labact-ok",
        )


@given(kind=st.sampled_from(tuple(IdentifierKind)), parts=IDENTIFIER_SUFFIX_STRATEGY)
def test_identifier_building_normalizes_suffixes_and_preserves_kind(
    kind: IdentifierKind, parts: list[str]
) -> None:
    identifier = build_identifier(kind, " ".join(parts))

    ensure_identifier_kind(identifier, kind)
    assert identifier == identifier.lower()
    assert " " not in identifier


@given(data=st.data(), raw_suffix=IDENTIFIER_RAW_SUFFIX_STRATEGY)
def test_identifier_classification_round_trips_and_rejects_wrong_kind(
    data: st.DataObject,
    raw_suffix: str,
) -> None:
    kind = data.draw(st.sampled_from(tuple(IdentifierKind)))
    wrong_kind = data.draw(
        st.sampled_from(
            tuple(candidate for candidate in IdentifierKind if candidate is not kind)
        )
    )

    identifier = build_identifier(kind, raw_suffix)

    assert classify_identifier(identifier) is kind
    assert identifier == f"{kind.value}-{raw_suffix.strip().lower().replace(' ', '-')}"

    ensure_identifier_kind(identifier, kind)
    with pytest.raises(ValueError, match=wrong_kind.value):
        ensure_identifier_kind(identifier, wrong_kind)


@given(
    kind=st.sampled_from(tuple(IdentifierKind)),
    blank_suffix=st.text(alphabet=" \t", min_size=0, max_size=8),
)
def test_identifier_building_rejects_blank_suffixes(
    kind: IdentifierKind,
    blank_suffix: str,
) -> None:
    with pytest.raises(ValueError, match="must be non-empty"):
        build_identifier(kind, blank_suffix)
