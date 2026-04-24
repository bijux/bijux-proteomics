# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Local provider implementations."""

from __future__ import annotations

__all__ = []

try:
    from bijux_proteomics_runtime.providers.local.esmfold import LocalESMFoldProvider
    from bijux_proteomics_runtime.providers.local.rosettafold import (
        LocalRoseTTAFoldProvider,
    )

    __all__ = ["LocalESMFoldProvider", "LocalRoseTTAFoldProvider"]
except ImportError:
    __all__ = []
