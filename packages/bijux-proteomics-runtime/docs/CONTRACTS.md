# Contracts

This document captures the public runtime contracts that downstream users and
integrators can rely on while migration proceeds.

## Public package identity

- Distribution name: `bijux-proteomics-runtime`
- Import root: `bijux_proteomics_runtime`
- Canonical CLI command: `bijux-proteomics-runtime`

## Public interface contracts

- `bijux_proteomics_runtime.interfaces.cli:cli` is the canonical CLI entrypoint.
- `bijux_proteomics_runtime.api.app:app` exposes the canonical FastAPI app.

## Stability commitments for this setup window

- Runtime entrypoints remain available and importable through this package.
- Runtime package documentation reflects ownership and dependency law.
- Runtime does not silently absorb lower-layer domain ownership.

## Non-goals for this setup window

- No compat deprecation policy is finalized in this document.
- No migration of domain semantics is implemented in this document.
- No long-term versioning policy override is introduced in this document.
