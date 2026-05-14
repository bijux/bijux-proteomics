from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.agentic_compatibility_inventory import (
    validate_agentic_compatibility_inventory,
)
from bijux_proteomics_dev.quality.architecture.runtime_boundaries import load_policy

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_agentic_compatibility_layer_is_wrapper_only_or_dead() -> None:
    issues = validate_agentic_compatibility_inventory(REPO_ROOT)
    assert not issues, "agentic compat inventory issues:\n" + "\n".join(
        f"{issue.code}: {issue.detail}" for issue in issues
    )


def test_agentic_compat_allowlist_is_empty_in_strict_mode() -> None:
    policy = load_policy(REPO_ROOT)
    allowlist_path = policy.compat_forwarding.non_forwarding_allowlist_path
    entries = [
        line.strip()
        for line in allowlist_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert not entries, (
        "strict compat mode requires zero allowlisted non-forwarding modules"
    )


def test_agentic_compat_forwarders_use_module_paths_not_init_modules() -> None:
    policy = load_policy(REPO_ROOT)
    failures: list[str] = []
    for path in sorted(policy.compat_forwarding.package_root.rglob("*.py")):
        content = path.read_text(encoding="utf-8")
        if ".__init__ import *" in content:
            failures.append(str(path.relative_to(REPO_ROOT)))
    assert not failures, (
        "compat forwarding modules must import package paths instead of __init__ modules:\n"
        + "\n".join(failures)
    )


def test_nested_compat_init_modules_stay_within_runtime_bridge_exports() -> None:
    policy = load_policy(REPO_ROOT)
    nested_init_paths = [
        policy.compat_forwarding.package_root / "agents" / "__init__.py",
        policy.compat_forwarding.package_root
        / "agents"
        / "coordination"
        / "__init__.py",
        policy.compat_forwarding.package_root / "execution" / "__init__.py",
        policy.compat_forwarding.package_root / "interfaces" / "http" / "__init__.py",
        policy.compat_forwarding.package_root / "orchestration" / "__init__.py",
        policy.compat_forwarding.package_root / "providers" / "local" / "__init__.py",
        policy.compat_forwarding.package_root / "providers" / "remote" / "__init__.py",
        policy.compat_forwarding.package_root / "state" / "__init__.py",
        policy.compat_forwarding.package_root / "tools" / "__init__.py",
    ]
    failures: list[str] = []
    for path in nested_init_paths:
        content = path.read_text(encoding="utf-8")
        if "agentic_proteins." in content:
            failures.append(str(path.relative_to(REPO_ROOT)))
            continue
        if "bijux_proteomics_runtime." not in content:
            failures.append(str(path.relative_to(REPO_ROOT)))
    assert not failures, (
        "nested compat __init__ modules must stay confined to runtime bridge exports:\n"
        + "\n".join(failures)
    )


def test_removed_compat_modules_do_not_return() -> None:
    removed_paths = [
        Path("packages/agentic-proteins/src/agentic_proteins/sandbox/__init__.py"),
    ]

    assert all(not (REPO_ROOT / path).exists() for path in removed_paths)
