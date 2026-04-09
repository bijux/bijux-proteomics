# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _workflow(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _matrix_include(job: dict[str, Any]) -> list[dict[str, Any]]:
    strategy = _as_dict(job.get("strategy"))
    matrix = _as_dict(strategy.get("matrix"))
    include = matrix.get("include")
    return include if isinstance(include, list) else []


def test_workflow_tree_is_standardized() -> None:
    root = _repo_root()
    workflows = root / ".github" / "workflows"
    found = {path.name for path in workflows.glob("*.yml")}
    assert found == {
        "build-release-artifacts.yml",
        "ci-package.yml",
        "deploy-docs.yml",
        "publish.yml",
        "verify.yml",
    }


def test_verify_workflow_uses_repo_contracts_and_package_matrix() -> None:
    root = _repo_root()
    workflow = _workflow(root / ".github" / "workflows" / "verify.yml")
    jobs = _as_dict(workflow.get("jobs"))
    repository = _as_dict(jobs.get("repository"))
    package = _as_dict(jobs.get("package"))

    assert repository.get("name") == "repository-contracts"
    assert package.get("uses") == "./.github/workflows/ci-package.yml"
    assert package.get("needs") == "repository"

    verify_packages = {
        entry["package_slug"] for entry in _matrix_include(package) if "package_slug" in entry
    }
    assert verify_packages == {
        "agentic-proteins",
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-dev",
    }

    dev = next(
        entry
        for entry in _matrix_include(package)
        if entry.get("package_slug") == "bijux-proteomics-dev"
    )
    assert dev.get("check_targets") == '["quality", "security", "build", "sbom"]'
