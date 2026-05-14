# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Remote provider implementations."""

from __future__ import annotations

from bijux_proteomics_runtime.providers.remote.colabfold import (
    APIColabFoldProvider,
)
from bijux_proteomics_runtime.providers.remote.openprotein import (
    APIOpenProteinProvider,
)
from bijux_proteomics_runtime.support.primitives.stability import experimental

experimental()

EXPERIMENTAL = True

__all__ = ["APIOpenProteinProvider", "APIColabFoldProvider", "EXPERIMENTAL"]
