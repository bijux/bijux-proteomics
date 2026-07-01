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


def test_make_tree_limits_python_helpers_to_shared_mirror() -> None:
    python_files = sorted(
        path.relative_to(REPO_ROOT / "makes")
        for path in (REPO_ROOT / "makes").rglob("*.py")
    )

    assert python_files == [Path("bijux-py/repository/artifact_aliases.py")]


def test_make_setup_routes_shared_hook_variables_through_dev_package() -> None:
    env_make = (REPO_ROOT / "makes" / "env.mk").read_text(encoding="utf-8")
    package_make = (REPO_ROOT / "makes" / "bijux-py" / "package.mk").read_text(
        encoding="utf-8"
    )
    repository_root_make = (
        REPO_ROOT / "makes" / "bijux-py" / "repository" / "root.mk"
    ).read_text(encoding="utf-8")

    assert "PROTEOMICS_ARTIFACT_LAYOUT_SCRIPT ?=" in env_make
    assert "bijux_proteomics_dev/workspace/artifact_layout.py" in env_make
    assert (
        "PACKAGE_ARTIFACT_ALIAS_SCRIPT ?= $(PROTEOMICS_ARTIFACT_LAYOUT_SCRIPT)"
        in env_make
    )
    assert (
        "ROOT_ARTIFACT_ALIAS_SCRIPT ?= $(PROTEOMICS_ARTIFACT_LAYOUT_SCRIPT)" in env_make
    )
    assert '"$(PYTHON)" "$(PACKAGE_ARTIFACT_ALIAS_SCRIPT)" package' in package_make
    assert '"$(PYTHON)" "$(ROOT_ARTIFACT_ALIAS_SCRIPT)" root' in repository_root_make


def test_package_make_installs_dependencies_through_venv_python() -> None:
    package_make = (REPO_ROOT / "makes" / "bijux-py" / "package.mk").read_text(
        encoding="utf-8"
    )

    assert (
        '--python "$(VENV_PYTHON)" --upgrade $(PACKAGE_INSTALL_BOOTSTRAP_PACKAGES)'
        in package_make
    )
    assert (
        '--python "$(VENV_PYTHON)" --upgrade $(PACKAGE_INSTALL_PYTHON_PACKAGES)'
        in package_make
    )
    assert (
        '--python "$(VENV_PYTHON)" --editable "$(PACKAGE_INSTALL_SPEC)"' in package_make
    )
