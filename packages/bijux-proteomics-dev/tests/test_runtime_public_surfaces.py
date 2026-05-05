from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _release_var(name: str) -> str:
    for line in (
        (REPO_ROOT / ".github" / "release.env").read_text(encoding="utf-8").splitlines()
    ):
        if line.startswith(f"{name}="):
            value = line.split("=", 1)[1].strip()
            return value.strip("'")
    raise AssertionError(f"missing release env variable: {name}")


def test_release_matrices_include_runtime_and_compat_roles() -> None:
    build_matrix = json.loads(_release_var("BIJUX_RELEASE_BUILD_MATRIX_JSON"))
    pypi_matrix = json.loads(_release_var("BIJUX_PYPI_PACKAGE_MATRIX_JSON"))
    ghcr_matrix = json.loads(_release_var("BIJUX_GHCR_RELEASE_PACKAGE_MATRIX_JSON"))

    build_slugs = {entry["package_slug"] for entry in build_matrix}
    assert "agentic-proteins" in build_slugs
    assert any(
        slug.startswith("bijux-proteomics-") and slug != "bijux-proteomics-dev"
        for slug in build_slugs
    )

    role_by_slug = {
        entry["package_slug"]: entry.get("release_role") for entry in build_matrix
    }
    assert role_by_slug.get("agentic-proteins") in {"compat", None}

    for matrix in (pypi_matrix, ghcr_matrix):
        slugs = {entry["package_slug"] for entry in matrix}
        assert "agentic-proteins" in slugs
        assert any(
            slug.startswith("bijux-proteomics-") and slug != "bijux-proteomics-dev"
            for slug in slugs
        )
        role_index = {
            entry["package_slug"]: entry.get("release_role") for entry in matrix
        }
        assert role_index.get("agentic-proteins") in {"compat", None}


def test_repository_docs_describe_runtime_as_canonical_and_agentic_as_compat() -> None:
    docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    platform_overview = (
        REPO_ROOT
        / "docs"
        / "01-bijux-proteomics"
        / "foundation"
        / "platform-overview.md"
    ).read_text(encoding="utf-8")
    compat_index = (REPO_ROOT / "docs" / "02-agentic-proteins" / "index.md").read_text(
        encoding="utf-8"
    )
    api_governance = (
        REPO_ROOT
        / "docs"
        / "01-bijux-proteomics"
        / "operations"
        / "api-and-schema-governance.md"
    ).read_text(encoding="utf-8")

    assert (
        "<code>bijux-proteomics-runtime</code> governs execution and replay."
        in docs_index
    )
    assert (
        "<code>agentic-proteins</code> preserves compatibility entrypoints."
        in docs_index
    )
    assert "`bijux-proteomics-runtime` governs execution, replay" in platform_overview
    assert "`agentic-proteins` is the strict compatibility package" in compat_index
    assert "apis/bijux-proteomics-runtime/v1/" in api_governance


def test_runtime_readme_mentions_integrity_outputs() -> None:
    readme = (
        REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "README.md"
    ).read_text(encoding="utf-8")

    assert "typed run context, artifact ledger, replay contract" in readme
    assert "preflight and failure reports" in readme
