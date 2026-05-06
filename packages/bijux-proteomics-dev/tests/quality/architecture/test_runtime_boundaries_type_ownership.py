from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import (
    check_runtime_type_collisions,
    load_policy,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_runtime_type_ownership_contract_has_no_current_collisions() -> None:
    policy = load_policy(REPO_ROOT)
    failures = check_runtime_type_collisions(policy)
    assert not failures, "runtime type ownership collisions:\n" + "\n".join(failures)


def test_runtime_type_overlap_allowlist_is_defined() -> None:
    policy = load_policy(REPO_ROOT)
    assert policy.runtime_type_ownership.runtime_type_overlap_allowlist_path.exists()
