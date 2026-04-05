# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared async/polling helpers for providers."""

from __future__ import annotations

import secrets
import time

from agentic_proteins.providers.base import _time_left


def sleep_with_backoff(
    deadline: float,
    backoff: float,
    *,
    jitter: float = 0.1,
    max_backoff: float = 10.0,
) -> tuple[float, float]:
    """Sleep with jittered backoff until the deadline; return (new_backoff, slept)."""
    remaining = _time_left(deadline)
    if remaining <= 0:
        return backoff, 0.0
    sleep_for = min(backoff + jitter * secrets.SystemRandom().random(), remaining)
    time.sleep(sleep_for)
    return min(backoff * 1.5, max_backoff), sleep_for


def sleep_with_retry_after(
    deadline: float,
    backoff: float,
    retry_after: float,
    *,
    jitter: float = 0.1,
    max_backoff: float = 10.0,
) -> tuple[float, float]:
    """Sleep using Retry-After with jitter/backoff fallback; return (new_backoff, slept)."""
    remaining = _time_left(deadline)
    if remaining <= 0:
        return backoff, 0.0
    sleep_for = max(retry_after, backoff + jitter * secrets.SystemRandom().random())
    sleep_for = min(sleep_for, remaining)
    time.sleep(sleep_for)
    return min(backoff * 1.5, max_backoff), sleep_for
