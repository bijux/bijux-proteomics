# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import string

import pytest
from pydantic import ValidationError

from bijux_proteomics_foundation.testing.skip_policy import (
    SkipCategory,
    import_or_skip,
)

from bijux_proteomics_foundation.outcomes.failures import (
    ErrorCategory,
    ErrorEnvelope,
    build_error_envelope_from_exception,
    summarize_exception_chain,
)
from bijux_proteomics_foundation.outcomes.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.outcomes.results import (
    OperationDisposition,
    OperationResult,
)
from bijux_proteomics_foundation.support.provenance import (
    ProvenancePointer,
    ProvenancePointerKind,
)
from bijux_proteomics_foundation.support.states import SupportState

hypothesis = import_or_skip(
    "hypothesis",
    category=SkipCategory.OPTIONAL_DEPENDENCY,
    reason="hypothesis is required for the outcome property-based test surface",
)
given = hypothesis.given
st = hypothesis.strategies

JSON_SCALAR_STRATEGY = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10_000, max_value=10_000),
    st.text(alphabet=string.ascii_letters + string.digits + "-_", max_size=12),
)
JSON_VALUE_STRATEGY = st.recursive(
    JSON_SCALAR_STRATEGY,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(
            st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=8),
            children,
            max_size=4,
        ),
    ),
    max_leaves=10,
)
JSON_OBJECT_STRATEGY = st.dictionaries(
    st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=8),
    JSON_VALUE_STRATEGY,
    max_size=5,
)
TOKEN_TEXT_STRATEGY = st.text(
    alphabet=string.ascii_lowercase + string.digits + "-_/",
    min_size=1,
    max_size=24,
)
SENTENCE_TEXT_STRATEGY = st.text(
    alphabet=string.ascii_letters + string.digits + " -_/",
    min_size=1,
    max_size=48,
).filter(lambda value: bool(value.strip()))
HEX_DIGEST_STRATEGY = st.text(
    alphabet="0123456789abcdef",
    min_size=64,
    max_size=64,
)


@st.composite
def provenance_pointer_strategy(draw: st.DrawFn) -> ProvenancePointer:
    return ProvenancePointer(
        pointer_kind=draw(st.sampled_from(tuple(ProvenancePointerKind))),
        locator=draw(TOKEN_TEXT_STRATEGY),
        pointer_role=draw(TOKEN_TEXT_STRATEGY),
        source_system=draw(TOKEN_TEXT_STRATEGY),
        fingerprint=draw(st.none() | HEX_DIGEST_STRATEGY),
        pointer_labels=tuple(
            draw(st.lists(TOKEN_TEXT_STRATEGY, min_size=0, max_size=4))
        ),
    )


@st.composite
def operation_refusal_strategy(
    draw: st.DrawFn,
    *,
    operation: str | None = None,
) -> OperationRefusal:
    return OperationRefusal(
        operation=operation or draw(TOKEN_TEXT_STRATEGY),
        kind=draw(st.sampled_from(tuple(RefusalKind))),
        code=draw(SENTENCE_TEXT_STRATEGY),
        reason=draw(SENTENCE_TEXT_STRATEGY),
        support_state=draw(
            st.sampled_from(
                (
                    SupportState.REFUSED,
                    SupportState.INCOMPLETE,
                    SupportState.LOSSY,
                    SupportState.AMBIGUOUS,
                )
            )
        ),
        reason_details=tuple(
            draw(st.lists(SENTENCE_TEXT_STRATEGY, min_size=0, max_size=4))
        ),
        recommended_actions=tuple(
            draw(st.lists(SENTENCE_TEXT_STRATEGY, min_size=0, max_size=4))
        ),
        provenance=tuple(
            draw(st.lists(provenance_pointer_strategy(), min_size=0, max_size=3))
        ),
    )


@st.composite
def operation_result_strategy(draw: st.DrawFn) -> OperationResult:
    operation = draw(TOKEN_TEXT_STRATEGY)
    summary = draw(SENTENCE_TEXT_STRATEGY)
    provenance = tuple(
        draw(st.lists(provenance_pointer_strategy(), min_size=0, max_size=3))
    )
    variant = draw(st.sampled_from(("success", "refused", "degraded")))

    if variant == "success":
        return OperationResult.success(
            operation=operation,
            summary=summary,
            provenance=provenance,
            output_fingerprint=draw(st.none() | HEX_DIGEST_STRATEGY),
        )
    if variant == "refused":
        return OperationResult.refused(
            operation=operation,
            summary=summary,
            refusal=draw(operation_refusal_strategy(operation=operation)),
            provenance=provenance,
        )
    return OperationResult.degraded_success(
        operation=operation,
        summary=summary,
        state=draw(
            st.sampled_from(
                (
                    SupportState.AMBIGUOUS,
                    SupportState.INCOMPLETE,
                    SupportState.LOSSY,
                )
            )
        ),
        degradation_reasons=tuple(
            draw(st.lists(SENTENCE_TEXT_STRATEGY, min_size=1, max_size=4))
        ),
        provenance=provenance,
        output_fingerprint=draw(st.none() | HEX_DIGEST_STRATEGY),
    )


def test_support_state_refusal_and_error_models_serialize_deterministically() -> None:
    pointer = ProvenancePointer(
        pointer_kind=ProvenancePointerKind.ARTIFACT,
        locator="artifacts/review/run-7.json",
        pointer_role="review_artifact",
        pointer_labels=("review", "canonical"),
    )
    refusal = OperationRefusal(
        operation="mzidentml_ingestion",
        kind=RefusalKind.UNSUPPORTED,
        code="Engine Timeout",
        reason="the engine output is incomplete",
        support_state=SupportState.INCOMPLETE,
        reason_details=("missing peptide evidence", "engine timeout"),
        recommended_actions=("retry with full export", "collect complete run log"),
        provenance=(pointer,),
    )
    envelope = ErrorEnvelope(
        category=ErrorCategory.RUNTIME,
        code="Engine Timeout",
        message="external engine did not complete before timeout",
        context=(("run_id", "run-77"), ("step_id", "search")),
        cause_chain=("timeout", "adapter"),
        provenance=(pointer,),
    )

    assert refusal.code == "engine_timeout"
    assert refusal.support_state is SupportState.INCOMPLETE
    assert envelope.code == "engine_timeout"
    assert envelope.context[0] == ("run_id", "run-77")
    assert envelope.cause_chain == ("timeout", "adapter")


@given(refusal=operation_refusal_strategy())
def test_operation_refusal_round_trips_with_nested_provenance(
    refusal: OperationRefusal,
) -> None:
    restored = OperationRefusal.model_validate_json(refusal.model_dump_json())

    assert restored == refusal
    assert restored.to_dict() == refusal.to_dict()


@given(result=operation_result_strategy())
def test_operation_result_round_trips_across_success_refusal_and_degraded_paths(
    result: OperationResult,
) -> None:
    restored = OperationResult.model_validate_json(result.model_dump_json())

    assert restored == result
    assert restored.to_dict() == result.to_dict()


@given(context=JSON_OBJECT_STRATEGY)
def test_error_envelope_round_trips_nested_context_deterministically(
    context: dict[str, object],
) -> None:
    envelope = ErrorEnvelope(
        category=ErrorCategory.RUNTIME,
        code="Degraded Context",
        message="context was preserved with explicit loss reporting",
        support_state=SupportState.LOSSY,
        retryable=True,
        context=tuple(sorted(context.items())),
        cause_chain=("outer failure", " inner detail ", ""),
    )

    restored = ErrorEnvelope.model_validate_json(envelope.model_dump_json())

    assert restored == envelope
    assert tuple(key for key, _ in restored.context) == tuple(sorted(context))


def test_shared_operation_result_distinguishes_success_refusal_and_degraded_success() -> (
    None
):
    pointer = ProvenancePointer(
        pointer_kind=ProvenancePointerKind.ARTIFACT,
        locator="artifacts/foundation/result.json",
        pointer_role="result_artifact",
    )
    refusal = OperationRefusal(
        operation="mzml_ingestion",
        kind=RefusalKind.UNSUPPORTED,
        code="unsupported construct",
        reason="the construct cannot be normalized honestly",
    )

    success = OperationResult.success(
        operation="hash_manifest",
        summary="hash computed successfully",
        provenance=(pointer,),
        output_fingerprint="a" * 64,
    )
    refused = OperationResult.refused(
        operation="mzml_ingestion",
        summary="normalization was refused",
        refusal=refusal,
    )
    degraded = OperationResult.degraded_success(
        operation="mztab_ingestion",
        summary="payload normalized with explicit loss reporting",
        state=SupportState.LOSSY,
        degradation_reasons=("native field loss", "vendor score omitted"),
        output_fingerprint="b" * 64,
    )

    assert success.disposition is OperationDisposition.SUCCESS
    assert refused.disposition is OperationDisposition.REFUSED
    assert degraded.disposition is OperationDisposition.DEGRADED_SUCCESS


def test_refusal_serialization_preserves_normalized_reason_codes() -> None:
    refusal = OperationRefusal(
        operation="search_ingestion",
        kind=RefusalKind.AMBIGUOUS,
        code="Engine Timeout",
        reason="the source export stopped before peptide-level evidence finished",
        reason_details=("run log truncated", "peptide section missing"),
    )

    restored = OperationRefusal.model_validate_json(refusal.model_dump_json())

    assert restored.code == "engine_timeout"
    assert restored.reason == refusal.reason


def test_error_envelopes_preserve_nested_exception_context_predictably() -> None:
    try:
        try:
            raise ValueError("missing scan id")
        except ValueError as error:
            raise RuntimeError("mzml normalization failed") from error
    except RuntimeError as error:
        envelope = build_error_envelope_from_exception(
            category=ErrorCategory.RUNTIME,
            code="Normalization Failure",
            error=error,
            context={"run_id": "run-22", "step_id": "ingest"},
        )
        chain = summarize_exception_chain(error)

    assert chain == (
        "RuntimeError: mzml normalization failed",
        "ValueError: missing scan id",
    )
    assert envelope.code == "normalization_failure"
    assert envelope.context == (("run_id", "run-22"), ("step_id", "ingest"))
    assert envelope.cause_chain == chain


def test_error_envelope_round_trips_degraded_context_with_deeper_exception_chain() -> (
    None
):
    try:
        try:
            try:
                raise ValueError("missing precursor evidence")
            except ValueError as error:
                raise LookupError("candidate resolution degraded") from error
        except LookupError as error:
            raise RuntimeError("decision brief normalization degraded") from error
    except RuntimeError as error:
        envelope = build_error_envelope_from_exception(
            category=ErrorCategory.RUNTIME,
            code="Degraded Context",
            error=error,
            context={
                "step": {"support": "lossy", "step_id": "review"},
                "run": {"run_id": "run-77"},
            },
            retryable=True,
            state=SupportState.LOSSY,
        )

    restored = ErrorEnvelope.model_validate_json(envelope.model_dump_json())

    assert restored == envelope
    assert restored.support_state is SupportState.LOSSY
    assert restored.retryable is True
    assert restored.context == (
        ("run", {"run_id": "run-77"}),
        ("step", {"step_id": "review", "support": "lossy"}),
    )
    assert restored.cause_chain == (
        "RuntimeError: decision brief normalization degraded",
        "LookupError: candidate resolution degraded",
        "ValueError: missing precursor evidence",
    )


def test_operation_result_rejects_inconsistent_disposition_state_combinations() -> None:
    with pytest.raises(ValidationError, match="must carry one refusal"):
        OperationResult(
            operation="ingest",
            disposition=OperationDisposition.REFUSED,
            support_state=SupportState.REFUSED,
            summary="ingestion refused",
        )
