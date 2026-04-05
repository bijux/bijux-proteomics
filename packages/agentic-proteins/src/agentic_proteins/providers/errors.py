# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider error types."""

from __future__ import annotations


class PredictionError(RuntimeError):
    """Custom exception for all prediction-related failures.

    Attributes:
        code: The error code.
    """

    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        """Initializes the custom exception.

        Args:
            message: A human-readable description of the error.
            code: A machine-readable error code to categorize the failure.
        """
        super().__init__(message)
        self.code = code
