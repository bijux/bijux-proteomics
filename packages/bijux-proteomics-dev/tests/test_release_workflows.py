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


def test_publish_workflow_covers_all_release_packages() -> None:
    root = _repo_root()
    expected = {
        "agentic-proteins",
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    }

    workflow = _workflow(root / ".github" / "workflows" / "publish.yml")
    jobs = _as_dict(workflow.get("jobs"))
    build = _as_dict(jobs.get("build"))
    publish = _as_dict(jobs.get("publish"))

    assert build.get("uses") == "./.github/workflows/build-release-artifacts.yml"
    assert publish.get("needs") == "build"
    assert publish.get("environment", {}).get("name") == "pypi"

    build_found = {
        entry["package_slug"]
        for entry in _matrix_include(build)
        if "package_slug" in entry
    }
    publish_found = {
        entry["package_slug"]
        for entry in _matrix_include(publish)
        if "package_slug" in entry
    }

    assert build_found == expected
    assert publish_found == expected


def test_publish_workflow_uses_package_scoped_builds_and_sboms() -> None:
    root = _repo_root()
    workflow = _workflow(root / ".github" / "workflows" / "publish.yml")
    build = _as_dict(_as_dict(workflow.get("jobs")).get("build"))

    for entry in _matrix_include(build):
        package_slug = entry.get("package_slug")
        assert isinstance(package_slug, str)
        package_dir = (
            "packages/agentic-proteins"
            if package_slug == "agentic-proteins"
            else f"packages/{package_slug}"
        )
        assert entry.get("package_dir") == package_dir
        assert entry.get("artifacts_dir") == f"artifacts/{package_slug}"
        assert entry.get("build_targets") == "build sbom"


def test_release_docs_match_shared_publish_workflow_contract() -> None:
    root = _repo_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    release_doc = (
        root / "docs" / "bijux-proteomics" / "operations" / "release-and-versioning.md"
    ).read_text(encoding="utf-8")

    assert "shared `publish.yml` workflow" in readme
    assert (
        "`publish.yml` builds and publishes each package through its matrix entries"
        in readme
    )
    assert "`PYPI_API_TOKEN`" in readme
    assert (
        "`publish.yml` is tag-triggered and publishes one matrix entry per package"
        in release_doc
    )
