from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import (
    _is_forwarding_module,
    check_agentic_compat_forwarding,
    load_policy,
    parse_python_module,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_agentic_compat_forwarding_is_enforced_by_allowlist_contract() -> None:
    policy = load_policy(REPO_ROOT)
    failures = check_agentic_compat_forwarding(policy)
    assert not failures, "agentic compat forwarding violations:\n" + "\n".join(failures)


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


def test_nested_compat_init_modules_must_be_forwarding_only() -> None:
    policy = load_policy(REPO_ROOT)
    nested_init_paths = [
        policy.compat_forwarding.package_root / "core" / "__init__.py",
        policy.compat_forwarding.package_root / "sandbox" / "__init__.py",
    ]
    failures: list[str] = []
    for path in nested_init_paths:
        tree = parse_python_module(path).tree
        if not _is_forwarding_module(
            tree, policy.compat_forwarding.forwarding_target_prefixes
        ):
            failures.append(str(path.relative_to(REPO_ROOT)))
    assert not failures, (
        "nested compat __init__ modules must forward only:\n" + "\n".join(failures)
    )
