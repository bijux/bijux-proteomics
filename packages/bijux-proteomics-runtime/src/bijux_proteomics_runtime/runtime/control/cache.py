# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime cache coordination for safe shared reuse."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


class RuntimeCacheClaim(JsonModel):
    """One persisted runtime cache claim."""

    model_config = ConfigDict(extra="forbid")

    cache_key: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    access_mode: str = Field(..., min_length=1)
    input_fingerprint: str = Field(..., min_length=1)


class RuntimeCacheDecision(JsonModel):
    """Decision for one runtime cache claim attempt."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reason: str = Field(..., min_length=1)
    claim_path: str = Field(..., min_length=1)
    holder_run_id: str | None = Field(default=None)


def claim_runtime_cache(
    cache_root: Path,
    *,
    cache_key: str,
    run_id: str,
    access_mode: str,
    input_fingerprint: str,
) -> RuntimeCacheDecision:
    """Claim one runtime cache key for shared read or exclusive write."""
    if access_mode not in {"shared_read", "exclusive_write"}:
        raise ValueError("access_mode must be shared_read or exclusive_write")
    claim_path = cache_root / "claims" / f"{cache_key}.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    if not claim_path.exists():
        write_json_atomic(
            claim_path,
            RuntimeCacheClaim(
                cache_key=cache_key,
                run_id=run_id,
                access_mode=access_mode,
                input_fingerprint=input_fingerprint,
            ).to_dict(),
        )
        return RuntimeCacheDecision(
            allowed=True,
            reason="cache key was unclaimed",
            claim_path=str(claim_path),
            holder_run_id=run_id,
        )
    existing = RuntimeCacheClaim.load_json(claim_path)
    if existing.run_id == run_id:
        return RuntimeCacheDecision(
            allowed=True,
            reason="same runtime run already holds the cache claim",
            claim_path=str(claim_path),
            holder_run_id=existing.run_id,
        )
    if (
        existing.access_mode == "shared_read"
        and access_mode == "shared_read"
        and existing.input_fingerprint == input_fingerprint
    ):
        return RuntimeCacheDecision(
            allowed=True,
            reason="matching shared-read claims may reuse the same cache safely",
            claim_path=str(claim_path),
            holder_run_id=existing.run_id,
        )
    return RuntimeCacheDecision(
        allowed=False,
        reason="cache claim would mix exclusive access or mismatched fingerprints",
        claim_path=str(claim_path),
        holder_run_id=existing.run_id,
    )


def release_runtime_cache_claim(cache_root: Path, *, cache_key: str, run_id: str) -> None:
    """Release one runtime cache claim when the holder finishes."""
    claim_path = cache_root / "claims" / f"{cache_key}.json"
    if not claim_path.exists():
        return
    existing = RuntimeCacheClaim.load_json(claim_path)
    if existing.run_id != run_id:
        return
    claim_path.unlink()


__all__ = [
    "RuntimeCacheClaim",
    "RuntimeCacheDecision",
    "claim_runtime_cache",
    "release_runtime_cache_claim",
]
