# Architecture

`bijux-proteomics-foundation` exists to centralize shared document primitives so
every higher-level package can serialize, fingerprint, and version its models
with the same rules.

Core design choices:

- schema metadata is explicit and model-attached
- canonical serialization is deterministic across runs
- compatibility checks are data-model aware, not file-path aware

This package is intentionally dependency-light and stable so upstream packages
can rely on it as a low-volatility contract surface.
