# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed LC-MS quality-control facade."""

from __future__ import annotations

from bijux_proteomics.lab.qc import reports as _reports
from bijux_proteomics.lab.qc.reports import *  # noqa: F401,F403

_stable_sha256 = _reports._stable_sha256
