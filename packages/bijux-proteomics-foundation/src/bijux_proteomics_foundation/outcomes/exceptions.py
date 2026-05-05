# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Contract errors shared across packages."""

from __future__ import annotations


class FoundationContractError(Exception):
    """Base error for shared foundation contracts."""


class ContractValidationError(FoundationContractError):
    """Raised when a contract payload violates a required rule."""


class ContractNotFoundError(FoundationContractError):
    """Raised when a required contract entity is missing."""


class ContractConflictError(FoundationContractError):
    """Raised when a contract operation conflicts with current state."""


class MigrationPathError(FoundationContractError):
    """Raised when a schema migration path is missing or malformed."""


class MigrationExecutionError(FoundationContractError):
    """Raised when a migration step fails during execution."""
