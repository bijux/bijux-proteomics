# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility facade for the canonical quantification review owner."""

from __future__ import annotations

from bijux_proteomics.quantification.provenance.replicate_qc import (
    build_replicate_and_batch_qc_report as build_replicate_and_batch_qc_report,
)
from bijux_proteomics.quantification.provenance.review import *  # noqa: F401,F403
