# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""HTTP API entry points."""

from __future__ import annotations

from bijux_proteomics_runtime.api.app import AppConfig, create_app
from agentic_proteins.core.stability import stable

stable()

__all__ = ["AppConfig", "create_app"]
