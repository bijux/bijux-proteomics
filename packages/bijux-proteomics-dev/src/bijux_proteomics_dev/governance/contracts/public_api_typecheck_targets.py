# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed typecheck targets for curated public API modules."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from os.path import relpath
from pathlib import Path
import sys
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_import_path,
    workspace_src_parents,
)
from bijux_proteomics_dev.security.trusted_process import run_text

__all__ = [
    "PUBLIC_API_TYPECHECK_TARGETS_PATH",
    "PublicApiTypecheckManifest",
    "PublicApiTypecheckReport",
    "PublicApiTypecheckTarget",
    "build_public_api_pyright_config",
    "build_public_api_typecheck_report",
    "load_public_api_typecheck_manifest",
    "run",
    "validate_public_api_typecheck_manifest",
]


PUBLIC_API_TYPECHECK_TARGETS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "public-api-typecheck-targets.toml"
)
PUBLIC_API_TYPECHECK_ARTIFACTS_DIR = (
    REPO_ROOT / "artifacts" / "root" / "public-api-typecheck"
)


@dataclass(frozen=True)
class PublicApiTypecheckTarget:
    """One governed public module included in the public API typecheck lane."""

    distribution_name: str
    module_name: str
    source_path: str

    @property
    def absolute_path(self) -> Path:
        return REPO_ROOT / self.source_path


@dataclass(frozen=True)
class PublicApiTypecheckManifest:
    """Governed checker configuration and curated public-module target list."""

    mypy_config_path: str
    mypy_cache_dir: str
    pyright_config_path: str
    targets: tuple[PublicApiTypecheckTarget, ...]


@dataclass(frozen=True)
class PublicApiTypecheckReport:
    """Resolved public API typecheck contract for check execution."""

    mypy_config_path: Path
    mypy_cache_dir: Path
    pyright_config_path: Path
    targets: tuple[PublicApiTypecheckTarget, ...]

    @property
    def target_paths(self) -> tuple[Path, ...]:
        return tuple(target.absolute_path for target in self.targets)


def load_public_api_typecheck_manifest(
    path: Path = PUBLIC_API_TYPECHECK_TARGETS_PATH,
) -> PublicApiTypecheckManifest:
    """Load the governed public API typecheck manifest from TOML."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    mypy_table = cast(dict[str, Any], data["mypy"])
    pyright_table = cast(dict[str, Any], data["pyright"])
    targets = tuple(
        PublicApiTypecheckTarget(
            distribution_name=str(item["distribution_name"]),
            module_name=str(item["module_name"]),
            source_path=str(item["source_path"]),
        )
        for item in cast(list[dict[str, Any]], data["target"])
    )
    return PublicApiTypecheckManifest(
        mypy_config_path=str(mypy_table["config_path"]),
        mypy_cache_dir=str(mypy_table["cache_dir"]),
        pyright_config_path=str(pyright_table["config_path"]),
        targets=targets,
    )


def build_public_api_typecheck_report(
    manifest: PublicApiTypecheckManifest | None = None,
) -> PublicApiTypecheckReport:
    """Resolve the manifest into absolute checker paths."""

    manifest = manifest or load_public_api_typecheck_manifest()
    return PublicApiTypecheckReport(
        mypy_config_path=REPO_ROOT / manifest.mypy_config_path,
        mypy_cache_dir=REPO_ROOT / manifest.mypy_cache_dir,
        pyright_config_path=REPO_ROOT / manifest.pyright_config_path,
        targets=manifest.targets,
    )


def validate_public_api_typecheck_manifest(
    report: PublicApiTypecheckReport | None = None,
) -> tuple[str, ...]:
    """Detect stale or malformed public API typecheck contract entries."""

    report = report or build_public_api_typecheck_report()
    failures: list[str] = []
    if not report.mypy_config_path.exists():
        failures.append(f"missing mypy public api config {report.mypy_config_path}")
    if not report.pyright_config_path.exists():
        failures.append(
            f"missing pyright public api config {report.pyright_config_path}"
        )
    seen_modules: set[str] = set()
    seen_paths: set[str] = set()
    with workspace_import_path():
        for target in report.targets:
            if target.module_name in seen_modules:
                failures.append(
                    f"duplicate public api typecheck module {target.module_name}"
                )
            seen_modules.add(target.module_name)
            if target.source_path in seen_paths:
                failures.append(
                    f"duplicate public api typecheck path {target.source_path}"
                )
            seen_paths.add(target.source_path)
            if not target.absolute_path.exists():
                failures.append(
                    f"missing public api typecheck path {target.source_path}"
                )
                continue
            expected_suffix = Path(*target.module_name.split(".")).with_suffix(".py")
            if not target.source_path.endswith(expected_suffix.as_posix()):
                failures.append(
                    f"module/path mismatch for {target.module_name}: {target.source_path}"
                )
                continue
            try:
                __import__(target.module_name)
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"failed to import public api typecheck module {target.module_name} ({exc})"
                )
    return tuple(failures)


def build_public_api_pyright_config(
    report: PublicApiTypecheckReport | None = None,
) -> dict[str, object]:
    """Render the checked-in pyright config for curated public API modules."""

    report = report or build_public_api_typecheck_report()
    config_dir = report.pyright_config_path.parent
    return {
        "include": [
            Path(relpath(target.absolute_path, config_dir)).as_posix()
            for target in report.targets
        ],
        "exclude": ["artifacts", "build", "dist", "docs", "site"],
        "pythonVersion": "3.11",
        "typeCheckingMode": "strict",
        "venvPath": Path(
            relpath(REPO_ROOT / "artifacts" / "root", config_dir)
        ).as_posix(),
        "venv": "check-venv",
        "executionEnvironments": [
            {
                "root": Path(relpath(REPO_ROOT, config_dir)).as_posix(),
                "extraPaths": [
                    Path(relpath(path, config_dir)).as_posix()
                    for path in workspace_src_parents()
                ],
            }
        ],
    }


def _render_pyright_config_text(report: PublicApiTypecheckReport) -> str:
    return json.dumps(build_public_api_pyright_config(report), indent=2) + "\n"


def _pyright_config_is_fresh(report: PublicApiTypecheckReport) -> bool:
    if not report.pyright_config_path.exists():
        return False
    return report.pyright_config_path.read_text(encoding="utf-8") == _render_pyright_config_text(report)


def _run_mypy(report: PublicApiTypecheckReport) -> int:
    report.mypy_cache_dir.mkdir(parents=True, exist_ok=True)
    PUBLIC_API_TYPECHECK_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(report.mypy_config_path),
        "--cache-dir",
        str(report.mypy_cache_dir),
        *(str(path) for path in report.target_paths),
    ]
    completed = run_text(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    output = completed.stdout
    if completed.stderr:
        output = f"{output}{completed.stderr}"
    (PUBLIC_API_TYPECHECK_ARTIFACTS_DIR / "mypy.log").write_text(
        output,
        encoding="utf-8",
    )
    if output:
        print(output, end="")
    return completed.returncode


def _run_pyright(report: PublicApiTypecheckReport) -> int:
    PUBLIC_API_TYPECHECK_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pyright",
        "--project",
        str(report.pyright_config_path),
    ]
    completed = run_text(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    output = completed.stdout
    if completed.stderr:
        output = f"{output}{completed.stderr}"
    (PUBLIC_API_TYPECHECK_ARTIFACTS_DIR / "pyright.log").write_text(
        output,
        encoding="utf-8",
    )
    if output:
        print(output, end="")
    return completed.returncode


def run(*, check: bool = False, write_pyright_config: bool = False) -> int:
    """Validate or refresh the curated public API typecheck contract."""

    report = build_public_api_typecheck_report()
    if write_pyright_config:
        bootstrap_failures = tuple(
            failure
            for failure in validate_public_api_typecheck_manifest(report)
            if not failure.startswith("missing pyright public api config ")
        )
        if bootstrap_failures:
            for failure in bootstrap_failures:
                print(failure)
            return 1
        report.pyright_config_path.write_text(
            _render_pyright_config_text(report),
            encoding="utf-8",
        )
        print(
            "wrote pyright public api config for "
            f"{len(report.targets)} public modules"
        )
        return 0
    failures = validate_public_api_typecheck_manifest(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if not _pyright_config_is_fresh(report):
        expected_path = PUBLIC_API_TYPECHECK_ARTIFACTS_DIR / "pyright-public-api.actual.json"
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        expected_path.write_text(_render_pyright_config_text(report), encoding="utf-8")
        print(
            "pyright public api config is stale; regenerate it from "
            "bijux_proteomics_dev.governance.contracts.public_api_typecheck_targets"
        )
        return 1
    if check:
        mypy_code = _run_mypy(report)
        if mypy_code != 0:
            return mypy_code
        return _run_pyright(report)
    print(
        "public api typecheck contract covers "
        f"{len(report.targets)} public modules"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate governed public API typecheck targets and run the mypy lane."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run the governed mypy check over curated public API modules.",
    )
    parser.add_argument(
        "--write-pyright-config",
        action="store_true",
        help="Rewrite the checked-in pyright config from the governed manifest.",
    )
    args = parser.parse_args()
    raise SystemExit(
        run(check=args.check, write_pyright_config=args.write_pyright_config)
    )
