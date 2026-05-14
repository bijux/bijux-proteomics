# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.outcomes.exceptions import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    FoundationContractError,
)


def test_foundation_contract_errors_share_common_base() -> None:
    assert issubclass(ContractValidationError, FoundationContractError)
    assert issubclass(ContractNotFoundError, FoundationContractError)
    assert issubclass(ContractConflictError, FoundationContractError)
