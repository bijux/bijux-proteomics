---
title: Runtime Migration Validation
audience: mixed
type: runbook
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-22
---

# Runtime Migration Validation

Use this runbook to validate canonical runtime migration integrity before
shipping release tags.

## Validation Command

Run the full migration validation suite from repository root:

```bash
make quality-runtime-migration-validation
```

This command verifies:

- runtime boundary contracts (lower layers cannot import runtime)
- migration ledger freshness and full module coverage
- API freeze contracts under `apis/*/v1`
- release matrix inclusion of canonical runtime and compatibility packages
- compatibility import, CLI, and API parity tests

## Coordinated Release Checklist

Use this order for coordinated release readiness:

1. Confirm package metadata and changelog entries for all impacted packages.
2. Run repository checks:
   - `make quality`
   - `make security`
   - `make test`
3. Run migration validation:
   - `make quality-runtime-migration-validation`
4. Verify release matrix coverage:
   - `BIJUX_RELEASE_BUILD_MATRIX_JSON`
   - `BIJUX_PYPI_PACKAGE_MATRIX_JSON`
   - `BIJUX_GHCR_RELEASE_PACKAGE_MATRIX_JSON`
5. Confirm canonical versus compatibility release language:
   - `bijux-proteomics-runtime` as canonical runtime package
   - `agentic-proteins` as compatibility package
6. Execute release dry-run workflows or controlled tag release.

## Purpose

This page defines a repeatable validation path that keeps runtime migration
contracts enforceable during coordinated releases.
