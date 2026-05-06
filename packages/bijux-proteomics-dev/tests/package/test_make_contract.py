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
    assert '"$(CURDIR)/configs/artifacts"' in repository_root_make
