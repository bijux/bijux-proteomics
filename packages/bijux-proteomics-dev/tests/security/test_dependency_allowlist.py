from __future__ import annotations

from pathlib import Path

from pytest import CaptureFixture

from bijux_proteomics_dev.security.dependency_allowlist import POLICY_PATH, run


def _write_project(repo_root: Path, dependencies: list[str]) -> None:
    rendered = ", ".join(f'"{dependency}"' for dependency in dependencies)
    (repo_root / "pyproject.toml").write_text(
        f"[project]\nname = \"repository\"\ndependencies = [{rendered}]\n",
        encoding="utf-8",
    )


def _write_policy(repo_root: Path, allowed: list[str]) -> None:
    path = repo_root / POLICY_PATH
    path.parent.mkdir(parents=True)
    rendered = ", ".join(f'"{dependency}"' for dependency in allowed)
    path.write_text(
        f'policy = "deny-by-default"\nallowed_distributions = [{rendered}]\n',
        encoding="utf-8",
    )


def test_empty_root_runtime_contract_is_valid(tmp_path: Path) -> None:
    _write_project(tmp_path, [])
    _write_policy(tmp_path, [])

    assert run(tmp_path) == 0


def test_matching_runtime_dependency_is_valid(tmp_path: Path) -> None:
    _write_project(tmp_path, ["Requests>=2.0"])
    _write_policy(tmp_path, ["requests"])

    assert run(tmp_path) == 0


def test_unapproved_runtime_dependency_fails(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    _write_project(tmp_path, ["requests>=2.0"])
    _write_policy(tmp_path, [])

    assert run(tmp_path) == 1
    assert "Root runtime dependencies missing from policy" in capsys.readouterr().err


def test_stale_policy_entry_fails(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    _write_project(tmp_path, [])
    _write_policy(tmp_path, ["requests"])

    assert run(tmp_path) == 1
    assert "Policy entries absent from root runtime dependencies" in capsys.readouterr().err


def test_missing_policy_fails(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    _write_project(tmp_path, [])

    assert run(tmp_path) == 1
    assert "Root runtime dependency policy missing" in capsys.readouterr().err


def test_malformed_policy_fails(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    _write_project(tmp_path, [])
    path = tmp_path / POLICY_PATH
    path.parent.mkdir(parents=True)
    path.write_text("allowed_distributions = [", encoding="utf-8")

    assert run(tmp_path) == 1
    assert "Root runtime dependency policy unreadable" in capsys.readouterr().err
