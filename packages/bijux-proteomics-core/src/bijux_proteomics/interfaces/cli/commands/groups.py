# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Root CLI group definitions."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.group("qc")
def qc_group() -> None:
    """Build operator-facing LC-MS QC reports and artifacts."""


@click.group("isotope-labeling")
def isotope_labeling_group() -> None:
    """Build stable-isotope labeling review outputs and quantification ledgers."""


@click.group("interpretation")
def interpretation_group() -> None:
    """Map protein tables onto governed biological annotation surfaces."""


@click.group("multiplex")
def multiplex_group() -> None:
    """Build multiplex reporter-ion import and matrix review outputs."""


@click.group("ptm")
def ptm_group() -> None:
    """Summarize PTM evidence, mapped sites, and occupancy outputs."""


@click.group("search-adapter")
def search_adapter_group() -> None:
    """Inspect and normalize search-engine-specific result tables."""


GROUPS = (
    qc_group,
    isotope_labeling_group,
    interpretation_group,
    multiplex_group,
    ptm_group,
    search_adapter_group,
)
