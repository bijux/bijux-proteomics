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
    publish_pypi = _as_dict(jobs.get("publish_pypi"))
    publish_ghcr = _as_dict(jobs.get("publish_ghcr"))
    release = _as_dict(jobs.get("release"))

    assert build.get("uses") == "./.github/workflows/build-release-artifacts.yml"
    assert publish_pypi.get("needs") == "build"
    assert publish_pypi.get("environment", {}).get("name") == "pypi"
    assert publish_pypi.get("permissions") == {
        "contents": "read",
        "id-token": "write",
    }
    assert publish_ghcr.get("needs") == "build"
    assert publish_ghcr.get("permissions") == {
        "contents": "read",
        "packages": "write",
    }
    assert release.get("needs") == ["build", "publish_pypi", "publish_ghcr"]
    assert release.get("permissions") == {"contents": "write"}
    release_steps = release.get("steps", [])

    publish_pypi_steps = publish_pypi.get("steps", [])
    assert any(
        isinstance(step, dict)
        and step.get("uses") == "pypa/gh-action-pypi-publish@release/v1"
        and step.get("with", {}).get("packages-dir")
        for step in publish_pypi_steps
    )
    assert all(
        isinstance(step, dict) and "password" not in step.get("with", {})
        for step in publish_pypi_steps
    )
    assert any(
        isinstance(step, dict)
        and step.get("uses") == "softprops/action-gh-release@v2"
        and step.get("with", {}).get("overwrite_files") is False
        for step in release_steps
    )

    build_found = {
        entry["package_slug"]
        for entry in _matrix_include(build)
        if "package_slug" in entry
    }
    publish_pypi_found = {
        entry["package_slug"]
        for entry in _matrix_include(publish_pypi)
        if "package_slug" in entry
    }
    publish_ghcr_found = {
        entry["package_slug"]
        for entry in _matrix_include(publish_ghcr)
        if "package_slug" in entry
    }

    assert build_found == expected
    assert publish_pypi_found == expected
    assert publish_ghcr_found == expected


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


def test_reusable_release_workflow_stages_nested_dist_outputs() -> None:
    root = _repo_root()
    workflow = _workflow(root / ".github" / "workflows" / "build-release-artifacts.yml")
    build_job = _as_dict(_as_dict(workflow.get("jobs")).get("build"))
    stage_step = next(
        step
        for step in build_job.get("steps", [])
        if step.get("name") == "Stage publish artifacts"
    )
    stage_script = stage_step.get("run", "")
    release_step = next(
        step
        for step in build_job.get("steps", [])
        if step.get("name") == "Stage GitHub release assets"
    )
    release_script = release_step.get("run", "")

    assert 'find "$dist_dir" -type f' in stage_script
    assert "No publish artifacts found under $dist_dir" in stage_script
    assert (
        'asset_name="${{ inputs.package_slug }}-dist-$(basename "$file_path")"'
        in release_script
    )
    assert 'sbom_dir="${ARTIFACTS_DIR}/sbom"' in release_script
    assert '${{ inputs.package_slug }}-sbom-prod.cdx.json' in release_script
    assert '${{ inputs.package_slug }}-sbom-dev.cdx.json' in release_script
    assert '${{ inputs.package_slug }}-sbom-summary.txt' in release_script
    assert ".github/tmp/${{ inputs.package_slug }}-release/**/*" in str(
        build_job.get("steps", [])
    )


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
    assert "PyPI trusted publishing" in readme
    assert "`publish.yml` also publishes one GHCR bundle per package" in readme
    assert (
        "`publish.yml` is tag-triggered and fans out into build, PyPI, GHCR, and GitHub Release jobs"
        in release_doc
    )
