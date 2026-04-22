from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import (
    check_lower_layer_runtime_imports,
    load_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_runtime_boundary_policy_loads_expected_import_roots() -> None:
    policy = load_policy(REPO_ROOT)
    roots = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in policy.runtime_imports.lower_layer_roots
    }
    assert "packages/bijux-proteomics-core/src" in roots
    assert "packages/bijux-proteomics-runtime/src" not in roots


def test_lower_layers_do_not_import_runtime_package() -> None:
    policy = load_policy(REPO_ROOT)
    failures = check_lower_layer_runtime_imports(policy)
    assert not failures, "runtime import direction violations:\n" + "\n".join(failures)
