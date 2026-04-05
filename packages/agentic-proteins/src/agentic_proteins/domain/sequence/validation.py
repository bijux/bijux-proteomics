# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""validation."""

from __future__ import annotations

ALLOWED_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def validate_sequence(sequence: str) -> list[str]:
    """validate_sequence."""
    errors: list[str] = []
    if not sequence:
        return ["empty_sequence"]
    if any(aa not in ALLOWED_AMINO_ACIDS for aa in sequence.upper()):
        errors.append("invalid_sequence")
    return errors
