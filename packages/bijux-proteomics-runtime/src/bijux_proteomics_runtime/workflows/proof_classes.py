# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared runtime proof class enum."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["RuntimeProofClass"]


class RuntimeProofClass(StrEnum):
    """Exact proof class for one runtime claim or artifact bundle."""

    RAW_EXECUTION = "raw_execution"
    IMPORT_BACKED_EXECUTION = "import_backed_execution"
    REPLAY_BACKED_EXECUTION = "replay_backed_execution"
    SIMULATION_ONLY = "simulation_only"
