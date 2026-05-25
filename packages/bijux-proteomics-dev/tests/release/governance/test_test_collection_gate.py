from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.release.governance import test_collection_gate


def test_workspace_pythonpath_includes_workspace_src_roots() -> None:
    pythonpath = test_collection_gate._workspace_pythonpath()

    assert "packages/agentic-proteins/src" in pythonpath
    assert "packages/bijux-proteomics-core/src" in pythonpath
    assert "packages/proteomics-runtime/src" in pythonpath


def test_build_collection_gate_report_runs_import_and_collection_per_package(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        test_collection_gate,
        "workspace_package_names",
        lambda: ("bijux-proteomics-core", "bijux-proteomics-foundation"),
    )
    package_tests_root = tmp_path / "packages"
    (package_tests_root / "bijux-proteomics-core" / "tests").mkdir(parents=True)
    (package_tests_root / "bijux-proteomics-foundation" / "tests").mkdir(parents=True)
    monkeypatch.setattr(
        test_collection_gate,
        "tests_root",
        lambda package_name: package_tests_root / package_name / "tests",
    )

    def fake_run_subprocess(
        command: tuple[str, ...],
        *,
        cwd: Path,
    ) -> tuple[bool, str]:
        if command[1:3] == ("-m", "pytest"):
            return True, "collected tests"
        return True, "imported package"

    monkeypatch.setattr(test_collection_gate, "_run_subprocess", fake_run_subprocess)

    report = test_collection_gate.build_test_collection_gate_report(
        repo_root=tmp_path,
        python_executable="/python",
    )

    assert [check.package_name for check in report.import_checks] == [
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
    ]
    assert [check.package_name for check in report.collection_checks] == [
        "workspace",
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
    ]
    assert report.failed_checks == ()
    assert report.collection_checks[0].target == "packages"
    assert report.collection_checks[1].target == "packages/bijux-proteomics-core/tests"
    assert report.import_checks[0].target == "bijux_proteomics"


def test_workspace_collection_check_uses_repo_root_pytest_entrypoint(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_subprocess(
        command: tuple[str, ...],
        *,
        cwd: Path,
    ) -> tuple[bool, str]:
        captured["command"] = command
        captured["cwd"] = cwd
        return True, "collected tests"

    monkeypatch.setattr(test_collection_gate, "_run_subprocess", fake_run_subprocess)

    check = test_collection_gate._workspace_collection_check(
        python_executable="/python",
        repo_root=tmp_path,
    )

    assert check.package_name == "workspace"
    assert check.target == "packages"
    assert captured["cwd"] == tmp_path
    assert captured["command"] == (
        "/python",
        "-m",
        "pytest",
        "--collect-only",
        "packages",
        "-q",
    )


def test_run_reports_failed_import_or_collection_checks(
    monkeypatch: MonkeyPatch,
    capsys: object,
) -> None:
    monkeypatch.setattr(
        test_collection_gate,
        "build_test_collection_gate_report",
        lambda repo_root, python_executable=None: test_collection_gate.CollectionGateReport(
            import_checks=(
                test_collection_gate.CollectionGateCheck(
                    check_kind="import",
                    package_name="bijux-proteomics-core",
                    target="bijux_proteomics",
                    command=("python", "-c", "import bijux_proteomics"),
                    ok=False,
                    detail="import failed",
                ),
            ),
            collection_checks=(
                test_collection_gate.CollectionGateCheck(
                    check_kind="collection",
                    package_name="bijux-proteomics-runtime",
                    target="packages/bijux-proteomics-runtime/tests",
                    command=("python", "-m", "pytest"),
                    ok=False,
                    detail="collection failed",
                ),
            ),
        ),
    )

    exit_code = test_collection_gate.run()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "test collection gate failed" in captured.out
    assert "[import] bijux-proteomics-core -> bijux_proteomics: import failed" in captured.out
    assert (
        "[collection] bijux-proteomics-runtime -> "
        "packages/bijux-proteomics-runtime/tests: collection failed"
        in captured.out
    )


def test_run_reports_success_when_every_check_passes(
    monkeypatch: MonkeyPatch,
    capsys: object,
) -> None:
    monkeypatch.setattr(
        test_collection_gate,
        "build_test_collection_gate_report",
        lambda repo_root, python_executable=None: test_collection_gate.CollectionGateReport(
            import_checks=(),
            collection_checks=(),
        ),
    )

    exit_code = test_collection_gate.run()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "test collection gate passed"
