from __future__ import annotations

from typing import Any, cast

from pydantic import ValidationError
import pytest

from agentic_proteins.biology.signals import SignalPayload, SignalType


def test_signal_payload_rejects_blank_source() -> None:
    with pytest.raises(ValueError, match="source_id"):
        SignalPayload(source_id="  ", signal_type=SignalType.ACTIVATE)


def test_signal_payload_rejects_blank_targets() -> None:
    with pytest.raises(ValueError, match="target ids"):
        SignalPayload(
            source_id="p1",
            targets=("ok", " "),
            signal_type=SignalType.ACTIVATE,
        )


def test_signal_payload_rejects_non_string_metadata_keys() -> None:
    with pytest.raises(ValidationError):
        invalid_metadata = cast(dict[str, Any], {1: "bad"})
        SignalPayload(
            source_id="p1",
            signal_type=SignalType.ACTIVATE,
            metadata=invalid_metadata,
        )


def test_signal_payload_accepts_string_metadata_keys() -> None:
    payload = SignalPayload(
        source_id="p1",
        signal_type=SignalType.ACTIVATE,
        metadata={"ok": "yes"},
    )
    assert payload.metadata["ok"] == "yes"
