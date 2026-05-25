from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.governance.package_shape import skip_policy


def test_workspace_package_tests_use_shared_skip_policy_helpers() -> None:
    assert skip_policy.validate_test_skip_policy() == ()


def test_skip_policy_validation_rejects_raw_pytest_skip(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    test_file = tmp_path / "packages" / "bijux-proteomics-core" / "tests" / "test_skip_surface.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "import pytest\n\n\ndef test_surface():\n    pytest.skip('blocked')\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        skip_policy,
        "workspace_package_names",
        lambda: ("bijux-proteomics-core",),
    )
    monkeypatch.setattr(
        skip_policy,
        "test_modules",
        lambda package_name: (test_file,),
    )

    assert skip_policy.validate_test_skip_policy(tmp_path) == (
        "packages/bijux-proteomics-core/tests/test_skip_surface.py:5 "
        "uses raw pytest.skip; route skips through "
        "bijux_proteomics_foundation.testing.skip_policy",
    )


def test_skip_policy_validation_rejects_raw_pytest_importorskip(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    test_file = (
        tmp_path
        / "packages"
        / "bijux-proteomics-runtime"
        / "tests"
        / "test_http_surface.py"
    )
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "import pytest\n\npytest.importorskip('httpx')\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        skip_policy,
        "workspace_package_names",
        lambda: ("bijux-proteomics-runtime",),
    )
    monkeypatch.setattr(
        skip_policy,
        "test_modules",
        lambda package_name: (test_file,),
    )

    assert skip_policy.validate_test_skip_policy(tmp_path) == (
        "packages/bijux-proteomics-runtime/tests/test_http_surface.py:3 "
        "uses raw pytest.importorskip; route skips through "
        "bijux_proteomics_foundation.testing.skip_policy",
    )
