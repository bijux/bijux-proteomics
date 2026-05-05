# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.hashing import (
    StableHashPolicy as WrapperStableHashPolicy,
    default_hash_policy as wrapper_default_hash_policy,
)
from bijux_proteomics_foundation.ids import (
    CycleId as WrapperCycleId,
    IdentifierKind as WrapperIdentifierKind,
    ensure_identifier_kind as wrapper_ensure_identifier_kind,
)
from bijux_proteomics_foundation.outcomes.refusals import (
    OperationRefusal as CanonicalOperationRefusal,
    RefusalKind as CanonicalRefusalKind,
)
from bijux_proteomics_foundation.outcomes.results import (
    OperationDisposition as CanonicalOperationDisposition,
    OperationResult as CanonicalOperationResult,
)
from bijux_proteomics_foundation.refusals import (
    OperationRefusal as WrapperOperationRefusal,
    RefusalKind as WrapperRefusalKind,
)
from bijux_proteomics_foundation.results import (
    OperationDisposition as WrapperOperationDisposition,
    OperationResult as WrapperOperationResult,
)
from bijux_proteomics_foundation.serialization.hashing import (
    StableHashPolicy as CanonicalStableHashPolicy,
    default_hash_policy as canonical_default_hash_policy,
)
from bijux_proteomics_foundation.identity.identifiers import (
    CycleId as CanonicalCycleId,
    IdentifierKind as CanonicalIdentifierKind,
    ensure_identifier_kind as canonical_ensure_identifier_kind,
)
from bijux_proteomics_foundation.states import SupportState as WrapperSupportState
from bijux_proteomics_foundation.support.states import SupportState as CanonicalSupportState


def test_live_hashing_wrapper_exports_alias_canonical_hashing_symbols() -> None:
    assert WrapperStableHashPolicy is CanonicalStableHashPolicy
    assert wrapper_default_hash_policy is canonical_default_hash_policy


def test_live_identifier_wrapper_exports_alias_canonical_identifier_symbols() -> None:
    assert WrapperCycleId is CanonicalCycleId
    assert WrapperIdentifierKind is CanonicalIdentifierKind
    assert wrapper_ensure_identifier_kind is canonical_ensure_identifier_kind


def test_live_refusal_wrapper_exports_alias_canonical_refusal_symbols() -> None:
    assert WrapperOperationRefusal is CanonicalOperationRefusal
    assert WrapperRefusalKind is CanonicalRefusalKind


def test_live_result_wrapper_exports_alias_canonical_result_symbols() -> None:
    assert WrapperOperationDisposition is CanonicalOperationDisposition
    assert WrapperOperationResult is CanonicalOperationResult


def test_live_state_wrapper_exports_alias_canonical_state_symbols() -> None:
    assert WrapperSupportState is CanonicalSupportState
