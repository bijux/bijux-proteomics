# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import JsonModel, hash_text
from bijux_proteomics_runtime.core.hashing import sha256_hex
from bijux_proteomics_runtime.runtime.contracts import SchemaFormatContract


def test_runtime_contracts_and_hashing_use_foundation_primitives() -> None:
    assert issubclass(SchemaFormatContract, JsonModel)
    assert sha256_hex("runtime") == hash_text("runtime")
