from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runtime.control import (
    RuntimeCacheClaim,
    claim_runtime_cache,
    release_runtime_cache_claim,
)


def test_runtime_cache_claim_allows_matching_shared_reads(tmp_path: Path) -> None:
    cache_root = tmp_path / "artifacts" / "cache"

    first = claim_runtime_cache(
        cache_root,
        cache_key="dia-library",
        run_id="run-a",
        access_mode="shared_read",
        input_fingerprint="fp-1",
    )
    second = claim_runtime_cache(
        cache_root,
        cache_key="dia-library",
        run_id="run-b",
        access_mode="shared_read",
        input_fingerprint="fp-1",
    )

    assert first.allowed is True
    assert second.allowed is True
    assert second.holder_run_id == "run-a"
    assert RuntimeCacheClaim.load_json(cache_root / "claims" / "dia-library.json").run_id == (
        "run-a"
    )


def test_runtime_cache_claim_refuses_unsafe_sharing(tmp_path: Path) -> None:
    cache_root = tmp_path / "artifacts" / "cache"

    claim_runtime_cache(
        cache_root,
        cache_key="dda-import",
        run_id="run-a",
        access_mode="exclusive_write",
        input_fingerprint="fp-1",
    )
    rejected = claim_runtime_cache(
        cache_root,
        cache_key="dda-import",
        run_id="run-b",
        access_mode="shared_read",
        input_fingerprint="fp-2",
    )

    assert rejected.allowed is False
    assert rejected.holder_run_id == "run-a"


def test_runtime_cache_claim_releases_only_for_the_holder(tmp_path: Path) -> None:
    cache_root = tmp_path / "artifacts" / "cache"
    claim_path = cache_root / "claims" / "quant-cache.json"
    claim_runtime_cache(
        cache_root,
        cache_key="quant-cache",
        run_id="run-a",
        access_mode="shared_read",
        input_fingerprint="fp-1",
    )

    release_runtime_cache_claim(cache_root, cache_key="quant-cache", run_id="run-b")
    assert claim_path.exists()

    release_runtime_cache_claim(cache_root, cache_key="quant-cache", run_id="run-a")
    assert not claim_path.exists()
