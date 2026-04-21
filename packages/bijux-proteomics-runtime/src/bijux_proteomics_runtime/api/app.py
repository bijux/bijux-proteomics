"""Minimal FastAPI app surface for canonical runtime ownership."""

from __future__ import annotations

from fastapi import FastAPI

from bijux_proteomics_runtime.runtime_identity import runtime_banner

app = FastAPI(title="bijux-proteomics-runtime", version="0")


@app.get("/health", tags=["runtime"])
def health() -> dict[str, str]:
    """Health endpoint for smoke and ownership checks."""
    return {"status": "ok", "runtime": runtime_banner()}
