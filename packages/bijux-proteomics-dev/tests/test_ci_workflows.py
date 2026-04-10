# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

WORKFLOW_URL_RE = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/actions/workflows/"
    r"(?P<workflow>[A-Za-z0-9_.-]+)"
)


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


def _workflow_docs(root: Path) -> list[Path]:
    package_root = root / "packages"
    return [
        root / "README.md",
        *sorted(package_root.glob("*/README.md")),
        *sorted(package_root.glob("*/docs/maintainer/pypi.md")),
    ]


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
        entry["package_slug"]
        for entry in _matrix_include(package)
        if "package_slug" in entry
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


def test_reusable_workflow_jobs_are_package_scoped() -> None:
    root = _repo_root()
    ci_workflow = _workflow(root / ".github" / "workflows" / "ci-package.yml")
    build_workflow = _workflow(
        root / ".github" / "workflows" / "build-release-artifacts.yml"
    )
    ci_jobs = _as_dict(ci_workflow.get("jobs"))
    build_jobs = _as_dict(build_workflow.get("jobs"))

    assert _as_dict(ci_jobs.get("tests")).get("name") == (
        "tests-${{ inputs.package_slug }}-py${{ matrix.python-version }}"
    )
    assert _as_dict(ci_jobs.get("checks")).get("name") == (
        "checks-${{ inputs.package_slug }}-${{ matrix.target }}"
    )
    assert _as_dict(ci_jobs.get("lint")).get("name") == "lint-${{ inputs.package_slug }}"
    assert _as_dict(build_jobs.get("build")).get("name") == (
        "build-release-artifacts-${{ inputs.package_slug }}"
    )


def test_markdown_workflow_links_track_checked_in_workflow_tree() -> None:
    root = _repo_root()
    expected_repo = "bijux/bijux-proteomics"
    expected_workflows = {
        path.name for path in (root / ".github" / "workflows").glob("*.yml")
    }
    failures: list[str] = []

    for path in _workflow_docs(root):
        text = path.read_text(encoding="utf-8")
        for match in WORKFLOW_URL_RE.finditer(text):
            repo_slug = match.group("repo")
            workflow_name = match.group("workflow")
            if repo_slug != expected_repo:
                failures.append(
                    f"{path.relative_to(root)}: expected repo slug "
                    f"{expected_repo}, found {repo_slug}"
                )
            if workflow_name not in expected_workflows:
                failures.append(
                    f"{path.relative_to(root)}: unknown workflow {workflow_name}"
                )

    root_readme = (root / "README.md").read_text(encoding="utf-8")
    root_workflows = {
        match.group("workflow") for match in WORKFLOW_URL_RE.finditer(root_readme)
    }
    assert {"verify.yml", "publish.yml", "deploy-docs.yml"} <= root_workflows
    assert not failures, "workflow doc links failed:\n" + "\n".join(failures)
