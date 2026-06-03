# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import re
import shlex

from click.testing import CliRunner

from bijux_proteomics.interfaces.cli import cli

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
TUTORIAL_PATH = (
    REPO_ROOT / "packages" / "bijux-proteomics-core" / "docs" / "SHIPPED-DEMO-CLI.md"
)


def _bash_commands(text: str) -> tuple[str, ...]:
    commands: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL):
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                commands.append(stripped)
    return tuple(commands)


def test_shipped_demo_cli_tutorial_runs_from_clean_checkout() -> None:
    text = TUTORIAL_PATH.read_text(encoding="utf-8")
    commands = _bash_commands(text)

    assert "bijux-proteomics demo --out-dir demo_result" in text
    assert "bijux-proteomics validate-result demo_result" in text
    assert "bijux-proteomics query-result demo_result" in text
    assert commands, "shipped demo CLI tutorial must contain runnable bash commands"

    runner = CliRunner()
    with runner.isolated_filesystem():
        for command in commands:
            argv = shlex.split(command)
            assert argv[0] == "bijux-proteomics"
            result = runner.invoke(cli, argv[1:])
            assert result.exit_code == 0, f"{command}\n{result.output}"

        demo_root = Path("demo_result")
        assert (demo_root / "surprising_demo_report.json").exists()
        assert (
            demo_root / "biological_review" / "biological_report_manifest.json"
        ).exists()
        assert (demo_root / "biological_review" / "biological_report.html").exists()
        assert (demo_root / "ptm_review" / "ptm_report_manifest.json").exists()

        validation_payload = json.loads(
            (demo_root / "result_validation.json").read_text(encoding="utf-8")
        )
        assert (demo_root / "result_manifest.json").exists()
        validation_summary = validation_payload["report"]["summary"]
        assert validation_summary["missing_required_file_count"] == 0
        assert validation_summary["source_report_count"] == 2
        assert (demo_root / "result_validation.summary.tsv").exists()
        assert (demo_root / "result_validation.warnings.tsv").exists()

        query_payload = json.loads(
            (demo_root / "query_result.json").read_text(encoding="utf-8")
        )
        assert query_payload["index"]["summary"]["ptm_site_document_count"] >= 1
        assert query_payload["report"]["summary"]["hit_count"] >= 1
        assert query_payload["report"]["hits"][0]["object_id"] == "P11111:S5:Phospho"
        assert (demo_root / "query_result.summary.tsv").exists()
        assert (demo_root / "query_result.hits.tsv").exists()
