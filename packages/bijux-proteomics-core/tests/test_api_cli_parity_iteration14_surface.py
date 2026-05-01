# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.runtime_iteration14 import evaluate_workflow_api_cli_parity


def test_evaluate_workflow_api_cli_parity_accepts_equal_action_payloads() -> None:
    payloads = {
        "plan": {"workflow_id": "wf-1", "step_count": 8},
        "run": {"run_id": "run-1", "status": "completed"},
        "inspect": {"artifacts": ["a", "b"]},
        "verify": {"verified": True},
        "replay": {"supported": True},
        "review": {"packet_id": "rp-1"},
    }

    report = evaluate_workflow_api_cli_parity(
        api_json_by_action=payloads,
        cli_json_by_action=dict(payloads),
    )

    assert report.parity is True
    assert not report.issues
