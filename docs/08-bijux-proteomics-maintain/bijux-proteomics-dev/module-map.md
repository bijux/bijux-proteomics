---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Module Map

The package is organized by repository-health concern so maintainers can find
the owning code path quickly.

## Current Modules

- `api/` for API freeze and OpenAPI drift enforcement
- `docs/` for markdown link checks, architecture consistency, and debt guards
- `quality/` for dependency analysis and repository quality policy
- `release/` for changelog and version consistency checks
- `security/` for vulnerability gating and dependency allowlist enforcement
- `tools/` for maintainer utility commands and reproducible helper flows
- `trusted_process.py` for shared maintainer-process support logic

