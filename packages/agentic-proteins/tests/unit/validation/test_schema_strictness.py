# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.domain.metrics.quality import QCStatus
from agentic_proteins.runtime.context import RunOutput, RunStatus, VersionInfo
from agentic_proteins.agents.schemas import CoordinatorDecisionType


def test_candidate_requires_identifier() -> None:
    with pytest.raises(ValidationError):
        Candidate(candidate_id="", sequence="ACDE")


def test_run_output_requires_candidate_id() -> None:
    with pytest.raises(ValidationError):
        RunOutput(
            run_id="run-1",
            candidate_id="",
            lifecycle_state="planned",
            status=RunStatus.SUCCESS,
            failure_type="none",
            plan_fingerprint="fp-1",
            tool_status="success",
            report={},
            qc_status=QCStatus.ACCEPTABLE,
            coordinator_decision=CoordinatorDecisionType.CONTINUE,
            errors=[],
            warnings=[],
            version_info=VersionInfo(
                app_version="0.1.0",
                git_commit="unknown",
                tool_versions={},
            ),
        )
