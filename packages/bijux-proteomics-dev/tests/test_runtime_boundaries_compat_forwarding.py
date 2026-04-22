from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import (
    check_agentic_compat_forwarding,
    load_policy,
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
    assert not entries, "strict compat mode requires zero allowlisted non-forwarding modules"
