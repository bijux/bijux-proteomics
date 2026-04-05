# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Domain exceptions for program and review flows."""

from __future__ import annotations


class BijuxProteomicsError(Exception):
    """Base exception for the core package."""


class ProgramValidationError(BijuxProteomicsError):
    """Raised when a program document fails domain validation."""


class ReviewGateBlockedError(BijuxProteomicsError):
    """Raised when execution is attempted before required review decisions exist."""
