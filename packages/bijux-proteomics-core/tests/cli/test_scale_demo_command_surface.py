# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from bijux_proteomics.interfaces.cli.app import cli


def test_demo_scale_command_runs_generated_local_scale_validation() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "demo-scale",
                "--out-dir",
                "proteomics_scale_demo",
                "--protein-count",
                "18",
                "--peptides-per-protein",
                "2",
                "--replicates-per-condition",
                "2",
                "--pathway-count",
                "6",
                "--summary-tsv-out",
                "proteomics_scale_demo.summary.tsv",
                "--stage-metrics-tsv-out",
                "proteomics_scale_demo.stages.tsv",
                "--validation-tsv-out",
                "proteomics_scale_demo.validation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["sample_count"] == 4
        assert payload["summary"]["protein_count"] == 18
        assert payload["summary"]["generated_feature_row_count"] == 144
        assert payload["summary"]["outputs_validated"] is True
        assert len(payload["stage_metrics"]) == 5
        assert Path("proteomics_scale_demo/scale_demo_report.json").exists()
        assert Path(
            "proteomics_scale_demo/biological_report/biological_report_manifest.json"
        ).exists()
        assert Path(
            "proteomics_scale_demo/biological_report/biological_evidence_graph_nodes.tsv"
        ).exists()
        assert Path(
            "proteomics_scale_demo/biological_report/biological_protein_cards.tsv"
        ).exists()
        assert "peak_memory_mib" in Path(
            "proteomics_scale_demo.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "build_report_bundle" in Path(
            "proteomics_scale_demo.stages.tsv"
        ).read_text(encoding="utf-8")
        assert "outputs_validated" in Path(
            "proteomics_scale_demo.validation.tsv"
        ).read_text(encoding="utf-8")
