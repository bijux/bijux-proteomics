from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_root_make_uses_shared_check_venv_location() -> None:
    root_make = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")
    repository_root_make = (
        REPO_ROOT / "makes" / "bijux-py" / "repository" / "root.mk"
    ).read_text(encoding="utf-8")

    assert "ROOT_CHECK_VENV := $(ROOT_ARTIFACTS_DIR)/check-venv" in root_make
    assert "ROOT_CHECK_VENV := $(CURDIR)/artifacts/.venv" not in root_make
    assert '"$(CURDIR)/configs/.pytest_cache"' in repository_root_make


def test_make_tree_stays_free_of_local_python_sources() -> None:
    assert list((REPO_ROOT / "makes").rglob("*.py")) == []


def test_make_setup_routes_repository_artifact_layout_through_dev_package() -> None:
    package_make = (REPO_ROOT / "makes" / "bijux-py" / "package.mk").read_text(
        encoding="utf-8"
    )
    repository_root_make = (
        REPO_ROOT / "makes" / "bijux-py" / "repository" / "root.mk"
    ).read_text(encoding="utf-8")

    assert "-m bijux_proteomics_dev.workspace.artifact_layout" in package_make
    assert "-m bijux_proteomics_dev.workspace.artifact_layout" in repository_root_make


def test_package_make_bootstraps_virtualenv_from_python_executable_target() -> None:
    package_make = (REPO_ROOT / "makes" / "bijux-py" / "package.mk").read_text(
        encoding="utf-8"
    )

    assert "$(VENV_PYTHON): | setup" in package_make
    assert "$(PACKAGE_INSTALL_STAMP): $(VENV_PYTHON)" in package_make
    assert "install: $(VENV_PYTHON)" in package_make
    assert "ensure-venv: $(VENV_PYTHON)" in package_make
