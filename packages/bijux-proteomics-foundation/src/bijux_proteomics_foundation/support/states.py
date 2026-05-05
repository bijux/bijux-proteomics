# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared operation-state vocabulary for support and loss reporting."""

from __future__ import annotations

from enum import StrEnum


class SupportState(StrEnum):
    """Shared state vocabulary for support, refusal, and degraded outcomes."""

    ADVISORY = "advisory"
    SUPPORTED = "supported"
    REFUSED = "refused"
    AMBIGUOUS = "ambiguous"
    INCOMPLETE = "incomplete"
    LOSSY = "lossy"


__all__ = ["SupportState"]
