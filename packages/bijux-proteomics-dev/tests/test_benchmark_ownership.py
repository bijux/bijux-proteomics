from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.benchmark_ownership import (
    load_benchmark_owners,
    validate_benchmark_owners,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_benchmark_owner_manifest_covers_each_workspace_package() -> None:
    owners = load_benchmark_owners(REPO_ROOT)
    package_names = {entry.package_name for entry in owners}

    assert len(owners) == 8
    assert package_names == {
        "agentic-proteins",
        "bijux-proteomics-dev",
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-runtime",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    }


def test_benchmark_owner_manifest_is_valid_for_current_repo() -> None:
    assert validate_benchmark_owners(REPO_ROOT) == ()
