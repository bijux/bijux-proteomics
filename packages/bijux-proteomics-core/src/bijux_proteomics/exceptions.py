# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Domain exceptions for program and review flows."""

from __future__ import annotations


class BijuxProteomicsError(Exception):
    """Base exception for the core package."""


class ProgramValidationError(BijuxProteomicsError):
    """Raised when a program document fails domain validation."""

    def __init__(self, message: str, *, issue_codes: list[str] | None = None) -> None:
        """Store a validation message plus stable issue-code identifiers."""
        super().__init__(message)
        self.issue_codes = issue_codes or []

    def __str__(self) -> str:
        """Render a compact error string with optional issue-code suffix."""
        if not self.issue_codes:
            return super().__str__()
        return f"{super().__str__()} ({', '.join(self.issue_codes)})"


class ReviewGateBlockedError(BijuxProteomicsError):
    """Raised when execution is attempted before required review decisions exist."""


class InvalidLifecycleTransitionError(BijuxProteomicsError):
    """Raised when a program lifecycle transition is not allowed."""
