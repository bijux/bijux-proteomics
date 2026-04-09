# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _workflow(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_ci_workflows_define_package_build_targets() -> None:
    root = _repo_root()
    workflows = root / ".github" / "workflows"
    package_ci_files = sorted(workflows.glob("ci-*.yml"))

    for path in package_ci_files:
        if path.name == "ci-package.yml":
            continue
        workflow = _workflow(path)
        uses = workflow["jobs"]["ci"]["uses"]
        assert uses == "./.github/workflows/ci-package.yml"
        build_target = workflow["jobs"]["ci"]["with"].get("build_target")
        assert isinstance(build_target, str)
        assert build_target.startswith("build-")


def test_agentic_workflow_watches_apis_directory() -> None:
    root = _repo_root()
    path = root / ".github" / "workflows" / "ci-agentic-proteins.yml"
    content = path.read_text(encoding="utf-8")
    assert '"apis/**"' in content
    assert '"api/**"' not in content
