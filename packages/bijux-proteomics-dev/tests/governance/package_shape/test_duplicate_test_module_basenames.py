from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.governance.package_shape import test_module_basenames


def test_workspace_duplicate_test_module_families_are_explicit_and_safe() -> None:
    families = test_module_basenames.build_duplicate_test_module_families()

    duplicate_names = {family.basename for family in families}
    repeated_same_package = {
        family.basename
        for family in families
        if len(set(family.package_names)) != len(family.package_names)
    }

    assert duplicate_names
    assert repeated_same_package == {
        "test_execution_surface.py",
        "test_provider_capability_registry_surface.py",
    }
    assert test_module_basenames.validate_duplicate_test_module_namespaces() == ()


def test_duplicate_test_module_namespace_validation_rejects_unpackaged_same_package_duplicates(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "packages" / "bijux-proteomics-core"
    tests_dir = package_root / "tests"
    study_dir = tests_dir / "study"
    targeted_dir = tests_dir / "targeted"
    study_dir.mkdir(parents=True)
    targeted_dir.mkdir(parents=True)
    study_file = study_dir / "test_shared_surface.py"
    targeted_file = targeted_dir / "test_shared_surface.py"
    study_file.write_text("def test_a():\n    pass\n", encoding="utf-8")
    targeted_file.write_text("def test_b():\n    pass\n", encoding="utf-8")

    monkeypatch.setattr(
        test_module_basenames,
        "workspace_package_names",
        lambda: ("bijux-proteomics-core",),
    )
    monkeypatch.setattr(
        test_module_basenames,
        "tests_root",
        lambda package_name: tests_dir,
    )
    monkeypatch.setattr(
        test_module_basenames,
        "package_test_modules",
        lambda package_name: (study_file, targeted_file),
    )

    issues = test_module_basenames.validate_duplicate_test_module_namespaces(tmp_path)

    assert issues == (
        "test_shared_surface.py repeats inside unpackaged test roots for "
        "bijux-proteomics-core: "
        "packages/bijux-proteomics-core/tests/study/test_shared_surface.py, "
        "packages/bijux-proteomics-core/tests/targeted/test_shared_surface.py",
    )


def test_duplicate_test_module_namespace_validation_allows_packaged_same_package_duplicates(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "packages" / "bijux-proteomics-runtime"
    tests_dir = package_root / "tests"
    parallel_dir = tests_dir / "parallel"
    streaming_dir = tests_dir / "streaming"
    parallel_dir.mkdir(parents=True)
    streaming_dir.mkdir(parents=True)
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    parallel_file = parallel_dir / "test_execution_surface.py"
    streaming_file = streaming_dir / "test_execution_surface.py"
    parallel_file.write_text("def test_a():\n    pass\n", encoding="utf-8")
    streaming_file.write_text("def test_b():\n    pass\n", encoding="utf-8")

    monkeypatch.setattr(
        test_module_basenames,
        "workspace_package_names",
        lambda: ("bijux-proteomics-runtime",),
    )
    monkeypatch.setattr(
        test_module_basenames,
        "tests_root",
        lambda package_name: tests_dir,
    )
    monkeypatch.setattr(
        test_module_basenames,
        "package_test_modules",
        lambda package_name: (parallel_file, streaming_file),
    )

    families = test_module_basenames.build_duplicate_test_module_families(tmp_path)

    assert len(families) == 1
    assert families[0].namespace_reason == "packaged-test-root"
    assert (
        test_module_basenames.validate_duplicate_test_module_namespaces(tmp_path) == ()
    )
