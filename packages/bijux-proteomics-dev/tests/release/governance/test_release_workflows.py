# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def test_release_docs_match_split_release_workflow_contract() -> None:
    root = _repo_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    release_doc = (
        root
        / "docs"
        / "01-bijux-proteomics"
        / "operations"
        / "release-and-versioning.md"
    ).read_text(encoding="utf-8")

    assert "release-artifacts.yml" in readme
    assert "release-pypi.yml" in readme
    assert "release-ghcr.yml" in readme
    assert "release-github.yml" in readme

    assert "release-artifacts.yml" in release_doc
    assert "release-pypi.yml" in release_doc
    assert "release-ghcr.yml" in release_doc
    assert "release-github.yml" in release_doc
    assert "publish.yml" not in release_doc
