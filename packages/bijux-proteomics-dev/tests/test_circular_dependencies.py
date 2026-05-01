from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.circular_dependencies import (
    find_workspace_dependency_cycles,
    validate_workspace_dependency_cycles,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _write_package(
    repo_root: Path,
    *,
    package_name: str,
    distribution_name: str,
    import_root: str,
    dependencies: tuple[str, ...],
) -> None:
    package_dir = repo_root / "packages" / package_name
    (package_dir / "src" / import_root).mkdir(parents=True, exist_ok=True)
    (package_dir / "src" / import_root / "__init__.py").write_text(
        '"""test package."""\n',
        encoding="utf-8",
    )
    dependency_block = ",\n".join(f'  "{dependency}",' for dependency in dependencies)
    pyproject = "\n".join(
        [
            "[project]",
            f'name = "{distribution_name}"',
            'version = "0.0.0"',
            "dependencies = [",
            dependency_block,
            "]",
            "",
        ]
    )
    (package_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")


def test_workspace_has_no_circular_package_dependencies() -> None:
    assert find_workspace_dependency_cycles(REPO_ROOT) == ()
    assert validate_workspace_dependency_cycles(REPO_ROOT) == ()


def test_cycle_detection_reports_declared_workspace_cycle(tmp_path: Path) -> None:
    (tmp_path / "packages").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[tool.bijux_proteomics]",
                'packages = ["pkg-a", "pkg-b", "pkg-c"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_package(
        tmp_path,
        package_name="pkg-a",
        distribution_name="pkg-a",
        import_root="pkg_a",
        dependencies=("pkg-b",),
    )
    _write_package(
        tmp_path,
        package_name="pkg-b",
        distribution_name="pkg-b",
        import_root="pkg_b",
        dependencies=("pkg-c",),
    )
    _write_package(
        tmp_path,
        package_name="pkg-c",
        distribution_name="pkg-c",
        import_root="pkg_c",
        dependencies=("pkg-a",),
    )

    issues = validate_workspace_dependency_cycles(tmp_path)

    assert len(issues) == 1
    assert issues[0].cycle == ("pkg-a", "pkg-b", "pkg-c")
    assert issues[0].detail == "pkg-a -> pkg-b -> pkg-c -> pkg-a"
