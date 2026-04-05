from __future__ import annotations

import json
from pathlib import Path

from agentic_proteins.runtime.infra.analysis import RunAnalysis


def test_run_analysis_records_and_writes(tmp_path: Path) -> None:
    analysis = RunAnalysis()
    analysis.record_candidate_event("cand-1", "start", {"detail": "x"})
    analysis.record_tool_result("tool", "success", 12.5)
    analysis.record_tool_result("tool", "failure", 5.0)
    analysis.record_iteration_delta(1, 0.12345, None)
    out_path = tmp_path / "analysis.json"
    analysis.write(out_path)

    payload = json.loads(out_path.read_text())
    assert payload["candidate_timeline"]["cand-1"][0]["event"] == "start"
    assert payload["tool_stats"]["tool"]["success"] == 1
    assert payload["tool_stats"]["tool"]["failure"] == 1
    assert payload["iteration_deltas"][0]["improvement_delta"] == 0.123
