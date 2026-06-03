from __future__ import annotations

import json

from bijux_proteomics_dev.governance.contracts.public_api_typecheck_targets import (
    PUBLIC_API_TYPECHECK_TARGETS_PATH,
    build_public_api_pyright_config,
    build_public_api_typecheck_report,
    load_public_api_typecheck_manifest,
    run,
    validate_public_api_typecheck_manifest,
)


def test_public_api_typecheck_manifest_covers_curated_public_modules() -> None:
    manifest = load_public_api_typecheck_manifest()

    assert [target.module_name for target in manifest.targets] == [
        "bijux_proteomics.public_api",
        "bijux_proteomics_foundation.public_api",
        "bijux_proteomics_foundation.support.public_api",
        "bijux_proteomics_intelligence.public_api",
        "bijux_proteomics_knowledge.public_api",
        "bijux_proteomics_knowledge.references.public",
        "bijux_proteomics_lab.public_api",
        "bijux_proteomics_runtime.public_api",
        "bijux_proteomics_runtime.api.public",
        "bijux_proteomics_runtime.execution.public",
        "bijux_proteomics_runtime.runs.public",
        "bijux_proteomics_runtime.workflows.public",
    ]


def test_public_api_typecheck_manifest_is_structurally_valid() -> None:
    report = build_public_api_typecheck_report()

    assert validate_public_api_typecheck_manifest(report) == ()


def test_public_api_typecheck_pyright_config_stays_in_sync() -> None:
    report = build_public_api_typecheck_report()
    expected = json.loads(report.pyright_config_path.read_text(encoding="utf-8"))

    assert build_public_api_pyright_config(report) == expected


def test_public_api_typecheck_run_passes_on_curated_public_modules() -> None:
    assert run(check=True) == 0


def test_public_api_typecheck_target_manifest_is_repository_owned() -> None:
    assert PUBLIC_API_TYPECHECK_TARGETS_PATH.as_posix().endswith(
        "configs/package-governance/public-api-typecheck-targets.toml"
    )
