from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW_URL_RE = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/actions/workflows/"
    r"(?P<workflow>[A-Za-z0-9_.-]+)"
)
EXPECTED_WORKFLOWS = {
    "automerge-pr.yml",
    "bijux-std.yml",
    "ci.yml",
    "deploy-docs.yml",
    "github-policy.yml",
    "pr-approval-policy.yml",
    "release-artifacts.yml",
    "release-ghcr.yml",
    "release-github.yml",
    "release-pypi.yml",
    "verify.yml",
}
EXPECTED_VERIFY_PACKAGES = {
    "agentic-proteins",
    "bijux-proteomics-foundation",
    "bijux-proteomics-core",
    "bijux-proteomics-intelligence",
    "bijux-proteomics-knowledge",
    "bijux-proteomics-lab",
    "bijux-proteomics-dev",
}


def _workflow(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    workflow: dict[str, Any] = {}
    for key, value in data.items():
        normalized_key = "on" if key is True else key
        if isinstance(normalized_key, str):
            workflow[normalized_key] = value
    return workflow


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _matrix_include(job: dict[str, Any]) -> list[dict[str, Any]]:
    strategy = _as_dict(job.get("strategy"))
    matrix = _as_dict(strategy.get("matrix"))
    include = matrix.get("include", [])
    return include if isinstance(include, list) else []


def _workflow_call_inputs(workflow: dict[str, Any]) -> dict[str, Any]:
    on_block = _as_dict(workflow.get("on"))
    workflow_call = on_block.get("workflow_call", {})
    return workflow_call.get("inputs", {}) if isinstance(workflow_call, dict) else {}


def _workflow_docs() -> list[Path]:
    package_root = REPO_ROOT / "packages"
    return [
        REPO_ROOT / "README.md",
        *sorted(package_root.glob("*/README.md")),
    ]


def _uses_setup_uv_with_lock_cache(step: Any) -> bool:
    if not isinstance(step, dict):
        return False
    uses = step.get("uses")
    if not isinstance(uses, str) or not uses.startswith("astral-sh/setup-uv@"):
        return False
    with_block = step.get("with", {})
    return (
        isinstance(with_block, dict)
        and with_block.get("cache-dependency-glob") == "uv.lock"
    )


def test_workflow_tree_is_standardized() -> None:
    found = {path.name for path in WORKFLOWS_DIR.glob("*.yml")}
    assert found == EXPECTED_WORKFLOWS


def test_verify_workflow_uses_repo_contract_job_and_package_matrix() -> None:
    workflow = _workflow(WORKFLOWS_DIR / "verify.yml")
    jobs = workflow.get("jobs", {})
    repository_job = _as_dict(jobs.get("repository"))
    package_job = _as_dict(jobs.get("package"))

    checks_steps = repository_job.get("steps", [])
    verify_step = next(
        (
            step
            for step in checks_steps
            if isinstance(step, dict)
            and str(step.get("name")) == "Verify repository automation contracts"
        ),
        {},
    )
    checks_command = str(_as_dict(verify_step).get("run", ""))
    assert "check-shared-bijux-py" in checks_command
    assert "check-config-layout" in checks_command
    assert "check-make-layout" in checks_command

    assert package_job.get("uses") == "./.github/workflows/ci.yml"
    include = _matrix_include(package_job)
    found = {entry["package_slug"] for entry in include}
    assert found == EXPECTED_VERIFY_PACKAGES

    dev = next(
        entry for entry in include if entry["package_slug"] == "bijux-proteomics-dev"
    )
    assert dev["check_targets"] == '["quality", "security", "build", "sbom"]'


def test_release_workflows_replace_legacy_publish_workflow() -> None:
    release_artifacts = _workflow(WORKFLOWS_DIR / "release-artifacts.yml")
    release_github = _workflow(WORKFLOWS_DIR / "release-github.yml")
    release_pypi = _workflow(WORKFLOWS_DIR / "release-pypi.yml")
    release_ghcr = _workflow(WORKFLOWS_DIR / "release-ghcr.yml")

    for workflow in (release_artifacts, release_github, release_pypi, release_ghcr):
        on_block = _as_dict(workflow.get("on"))
        push_block = _as_dict(on_block.get("push"))
        if push_block:
            tags = push_block.get("tags", [])
            assert isinstance(tags, list)
            assert "v*" in tags
            assert "workflow_dispatch" in on_block
        assert "workflow_call" in on_block

    assert release_artifacts.get("name") == "release-artifacts"
    assert release_artifacts["jobs"]["build"]["name"] == (
        "release-artifacts-${{ inputs.package_slug }}"
    )

    assert release_github.get("name") == "release-github"
    assert release_github["jobs"]["release"]["name"] == "github-release"

    assert release_pypi.get("name") == "release-pypi"
    assert release_pypi["jobs"]["resolve"]["name"] == "resolve-release-pypi-config"
    assert release_pypi["jobs"]["publish_artifact"]["name"].startswith("publish-pypi-")

    assert release_ghcr.get("name") == "release-ghcr"
    assert release_ghcr["jobs"]["resolve"]["name"] == "resolve-release-ghcr-config"
    assert release_ghcr["jobs"]["publish"]["name"].startswith("publish-ghcr-")
    assert release_ghcr["jobs"]["publish"]["permissions"] == {
        "contents": "read",
        "packages": "write",
    }


def test_ci_workflow_jobs_use_uv_cache_contract() -> None:
    ci_wrapper = _workflow(WORKFLOWS_DIR / "ci.yml")
    verify_workflow = _workflow(WORKFLOWS_DIR / "verify.yml")
    build_workflow = _workflow(WORKFLOWS_DIR / "release-artifacts.yml")
    docs_workflow = _workflow(WORKFLOWS_DIR / "deploy-docs.yml")
    ci_jobs = _as_dict(ci_wrapper.get("jobs"))
    assert {"tests", "checks", "lint"} <= set(ci_jobs)

    assert verify_workflow["jobs"]["repository"]["name"] == "repository-contracts"
    assert build_workflow["jobs"]["build"]["name"] == (
        "release-artifacts-${{ inputs.package_slug }}"
    )

    cache_checked_jobs = [
        ci_jobs["tests"],
        ci_jobs["checks"],
        ci_jobs["lint"],
        verify_workflow["jobs"]["repository"],
        build_workflow["jobs"]["build"],
        docs_workflow["jobs"]["build"],
    ]

    for job in cache_checked_jobs:
        if "uses" in job:
            continue
        steps = job.get("steps", [])
        assert any(_uses_setup_uv_with_lock_cache(step) for step in steps), (
            "workflow job is missing setup-uv"
        )

    inputs = _workflow_call_inputs(ci_wrapper)
    assert "cache_dependency_path" not in inputs
    build_inputs = _workflow_call_inputs(build_workflow)
    assert "cache_dependency_path" not in build_inputs
    assert "upload_paths" not in build_inputs
    assert "makefile_path" in build_inputs


def test_markdown_workflow_links_track_checked_in_workflow_tree() -> None:
    expected_repo = "bijux/bijux-proteomics"
    expected_workflows = {path.name for path in WORKFLOWS_DIR.glob("*.yml")}
    failures: list[str] = []

    for path in _workflow_docs():
        text = path.read_text(encoding="utf-8")
        for match in WORKFLOW_URL_RE.finditer(text):
            repo_slug = match.group("repo")
            workflow_name = match.group("workflow")
            if repo_slug != expected_repo:
                failures.append(
                    f"{path.relative_to(REPO_ROOT)}: expected repo slug "
                    f"{expected_repo}, found {repo_slug}"
                )
            if workflow_name not in expected_workflows:
                failures.append(
                    f"{path.relative_to(REPO_ROOT)}: unknown workflow {workflow_name}"
                )

    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    root_workflows = {
        match.group("workflow") for match in WORKFLOW_URL_RE.finditer(root_readme)
    }
    assert {"verify.yml", "release-github.yml", "deploy-docs.yml"} <= root_workflows
    assert not failures, "workflow doc links failed:\n" + "\n".join(failures)
