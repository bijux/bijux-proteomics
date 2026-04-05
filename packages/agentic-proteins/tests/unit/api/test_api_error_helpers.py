# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest
from fastapi import status

from agentic_proteins.api import errors as errors_module


def test_map_exception_variants() -> None:
    assert errors_module.map_exception(errors_module.HumanReviewRequiredError()) == (
        status.HTTP_202_ACCEPTED,
        "human_review_required",
    )
    assert errors_module.map_exception(FileNotFoundError()) == (
        status.HTTP_404_NOT_FOUND,
        "not_found",
    )
    assert errors_module.map_exception(ValueError()) == (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "invalid_input",
    )
    assert errors_module.map_exception(RuntimeError()) == (
        status.HTTP_409_CONFLICT,
        "conflict",
    )
    assert errors_module.map_exception(Exception()) == (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "unexpected",
    )


def test_raise_http_error_payload() -> None:
    with pytest.raises(errors_module.ApiError) as excinfo:
        errors_module.raise_http_error(ValueError("bad"), instance="/run")
    err = excinfo.value
    assert err.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert err.payload["error"]["title"] == "Validation error"


def test_error_envelopes() -> None:
    payload = errors_module.validation_error("bad", instance="/run")
    assert payload["error"]["title"] == "Validation error"
    payload = errors_module.method_not_allowed("nope", instance="/run")
    assert payload["error"]["title"] == "Method not allowed"
    payload = errors_module.http_error(
        status.HTTP_400_BAD_REQUEST, "bad", instance="/run"
    )
    assert payload["error"]["title"] == "Bad request"
    payload = errors_module.http_error(
        status.HTTP_404_NOT_FOUND, "missing", instance="/run"
    )
    assert payload["error"]["title"] == "Not found"
    payload = errors_module.http_error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid", instance="/run"
    )
    assert payload["error"]["title"] == "Validation error"
    payload = errors_module.ok_envelope({"status": "ok"}, meta={"a": 1})
    assert payload["status"] == "ok"
    assert payload["data"]["status"] == "ok"
