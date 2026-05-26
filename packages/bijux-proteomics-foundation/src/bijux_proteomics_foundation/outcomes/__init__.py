# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for shared refusal, failure, and result contracts."""

from __future__ import annotations

from bijux_proteomics_foundation.outcomes.exceptions import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    FoundationContractError,
    MissingOptionalDependencyError,
    MigrationExecutionError,
    MigrationPathError,
)
from bijux_proteomics_foundation.outcomes.failures import (
    ErrorCategory,
    ErrorEnvelope,
    build_error_envelope_from_exception,
    summarize_exception_chain,
)
from bijux_proteomics_foundation.outcomes.optional_dependencies import (
    import_optional_module,
    is_missing_optional_dependency_error,
)
from bijux_proteomics_foundation.outcomes.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.outcomes.results import (
    OperationDisposition,
    OperationResult,
)

__all__ = [
    "ContractConflictError",
    "ContractNotFoundError",
    "ContractValidationError",
    "ErrorCategory",
    "ErrorEnvelope",
    "FoundationContractError",
    "import_optional_module",
    "is_missing_optional_dependency_error",
    "MigrationExecutionError",
    "MigrationPathError",
    "MissingOptionalDependencyError",
    "OperationDisposition",
    "OperationRefusal",
    "OperationResult",
    "RefusalKind",
    "build_error_envelope_from_exception",
    "summarize_exception_chain",
]
