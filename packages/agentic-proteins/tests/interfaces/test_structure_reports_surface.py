# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.interfaces.structure_reports import Metrics, Report, nl_summary
from bijux_proteomics.structure_report import Metrics as RuntimeMetrics
from bijux_proteomics.structure_report import Report as RuntimeReport
from bijux_proteomics.structure_report.render import nl_summary as runtime_nl_summary


def test_structure_report_surface_forwards_to_canonical_owners() -> None:
    assert Report is RuntimeReport
    assert Metrics is RuntimeMetrics
    assert nl_summary is runtime_nl_summary
