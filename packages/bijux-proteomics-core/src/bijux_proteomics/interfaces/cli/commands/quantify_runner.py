# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Quantification runner shared by the split quantify command."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.quantify_runner import run_quantify_command
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
