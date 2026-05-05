# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import agentic_proteins as pkg
import agentic_proteins.core as compat_core
import bijux_proteomics.structure_report as structure_report
import bijux_proteomics_runtime.core as runtime_core
from bijux_proteomics_intelligence.interpretation.structures import (
    low_confidence_segments,
)


def test_package_exports() -> None:
    assert "Report" in pkg.__all__
    assert isinstance(pkg.__version__, str)


def test_core_package_forwards_to_runtime_exports() -> None:
    assert compat_core.CostSummary is runtime_core.CostSummary
    assert compat_core.FailureType is runtime_core.FailureType
    assert compat_core.ExecutionStatus is runtime_core.ExecutionStatus


def test_root_package_routes_report_conveniences_through_core() -> None:
    assert pkg.Report is structure_report.Report
    assert pkg.Metrics is structure_report.Metrics


def test_root_package_routes_confidence_convenience_through_intelligence() -> None:
    assert pkg.low_confidence_segments is low_confidence_segments
