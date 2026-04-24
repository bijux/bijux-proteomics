# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""HTTP error mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NoReturn

from fastapi import status
from pydantic import AnyUrl

from bijux_proteomics_runtime.api.v1.schema import ApiEnvelope, ErrorResponse

ErrorType = Literal[
    "invalid_input",
    "not_found",
    "conflict",
    "human_review_required",
    "unexpected",
]


@dataclass(frozen=True)
class ApiError(Exception):
    """ApiError."""

    status_code: int
    payload: dict[str, str]


class HumanReviewRequiredError(RuntimeError):
    """HumanReviewRequiredError."""


_ERROR_TITLES: dict[ErrorType, str] = {
    "invalid_input": "Validation error",
    "not_found": "Not found",
    "conflict": "Conflict",
    "human_review_required": "Human review required",
    "unexpected": "Internal server error",
}

_ERROR_TYPES: dict[ErrorType, AnyUrl] = {
    "invalid_input": AnyUrl("https://bijux-cli.dev/docs/errors/validation-error"),
    "not_found": AnyUrl("https://bijux-cli.dev/docs/errors/not-found"),
    "conflict": AnyUrl("https://bijux-cli.dev/docs/errors/conflict"),
    "human_review_required": AnyUrl(
        "https://bijux-cli.dev/docs/errors/human-review-required"
    ),
    "unexpected": AnyUrl("https://bijux-cli.dev/docs/errors/internal-error"),
}

_METHOD_NOT_ALLOWED_TYPE = AnyUrl(
    "https://bijux-cli.dev/docs/errors/method-not-allowed"
)
_BAD_REQUEST_TYPE = AnyUrl("https://bijux-cli.dev/docs/errors/bad-request")


def map_exception(exc: Exception) -> tuple[int, ErrorType]:
    """map_exception."""
    if isinstance(exc, HumanReviewRequiredError):
        return status.HTTP_202_ACCEPTED, "human_review_required"
    if isinstance(exc, FileNotFoundError):
        return status.HTTP_404_NOT_FOUND, "not_found"
    if isinstance(exc, ValueError):
        return status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_input"
    if isinstance(exc, RuntimeError):
        return status.HTTP_409_CONFLICT, "conflict"
    return status.HTTP_500_INTERNAL_SERVER_ERROR, "unexpected"


def _build_error(
    error_type: ErrorType, status_code: int, detail: str, instance: str
) -> dict[str, Any]:
    """_build_error."""
    return ErrorResponse(
        type=_ERROR_TYPES[error_type],
        title=_ERROR_TITLES[error_type],
        status=status_code,
        detail=detail,
        instance=instance,
    ).model_dump(mode="json")


def raise_http_error(exc: Exception, instance: str) -> NoReturn:
    """raise_http_error."""
    status_code, error_type = map_exception(exc)
    detail = _build_error(error_type, status_code, str(exc), instance)
    payload = ApiEnvelope(
        status="error",
        data=None,
        error=ErrorResponse.model_validate(detail),
        meta={},
    ).model_dump(mode="json")
    raise ApiError(status_code=status_code, payload=payload) from exc


def validation_error(detail: str, instance: str) -> dict[str, Any]:
    """validation_error."""
    error = _build_error(
        "invalid_input", status.HTTP_422_UNPROCESSABLE_CONTENT, detail, instance
    )
    return ApiEnvelope(
        status="error",
        data=None,
        error=ErrorResponse.model_validate(error),
        meta={},
    ).model_dump(mode="json")


def method_not_allowed(detail: str, instance: str) -> dict[str, Any]:
    """method_not_allowed."""
    error = ErrorResponse(
        type=_METHOD_NOT_ALLOWED_TYPE,
        title="Method not allowed",
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=detail,
        instance=instance,
    ).model_dump(mode="json")
    return ApiEnvelope(
        status="error",
        data=None,
        error=ErrorResponse.model_validate(error),
        meta={},
    ).model_dump(mode="json")


def http_error(status_code: int, detail: str, instance: str) -> dict[str, Any]:
    """http_error."""
    title = "HTTP error"
    error_type = _ERROR_TYPES["unexpected"]
    if status_code == status.HTTP_400_BAD_REQUEST:
        title = "Bad request"
        error_type = _BAD_REQUEST_TYPE
    elif status_code == status.HTTP_404_NOT_FOUND:
        title = "Not found"
        error_type = _ERROR_TYPES["not_found"]
    elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        title = "Method not allowed"
        error_type = _METHOD_NOT_ALLOWED_TYPE
    elif status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        title = "Validation error"
        error_type = _ERROR_TYPES["invalid_input"]
    error = ErrorResponse(
        type=error_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
    ).model_dump(mode="json")
    return ApiEnvelope(
        status="error",
        data=None,
        error=ErrorResponse.model_validate(error),
        meta={},
    ).model_dump(mode="json")


def ok_envelope(
    data: dict[str, Any], meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    """ok_envelope."""
    return {"status": "ok", "data": data, "error": None, "meta": meta or {}}
