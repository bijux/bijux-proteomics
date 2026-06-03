# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Domain exceptions for program and review flows."""

from __future__ import annotations

from enum import StrEnum


class BijuxProteomicsError(Exception):
    """Base exception for the core package."""


class SchemaError(BijuxProteomicsError):
    """Raised when a scientific document or table contract is invalid."""


class DesignError(BijuxProteomicsError):
    """Raised when declared sample, contrast, or validation design is inconsistent."""


class ScientificEvidenceError(BijuxProteomicsError):
    """Raised when required archived or linked scientific evidence is missing."""


class UnsupportedFormatError(BijuxProteomicsError):
    """Raised when a scientific format or schema version is unsupported."""


class InvalidWorkflowError(BijuxProteomicsError):
    """Raised when a workflow boundary cannot execute or rehydrate coherently."""


class ProteomicsOperatorErrorCode(StrEnum):
    """Stable operator-facing error codes for CLI and workflow surfaces."""

    INPUT_FASTA_REJECTED = "INPUT_FASTA_REJECTED"
    INPUT_DESIGN_INVALID = "INPUT_DESIGN_INVALID"
    QC_POLICY_INVALID = "QC_POLICY_INVALID"
    QC_SAMPLE_NOT_FOUND = "QC_SAMPLE_NOT_FOUND"
    QC_BUILD_FAILED = "QC_BUILD_FAILED"
    QC_OUTPUT_WRITE_FAILED = "QC_OUTPUT_WRITE_FAILED"


class ProteomicsOperatorError(BijuxProteomicsError):
    """Raised for operator-facing failures with a stable error code."""

    def __init__(self, code: ProteomicsOperatorErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        return f"{self.code.value}: {super().__str__()}"


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
