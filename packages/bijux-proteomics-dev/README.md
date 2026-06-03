# bijux-proteomics-dev

`bijux-proteomics-dev` is the maintenance toolkit for this monorepo. It owns
maintainer automation, docs checks, and release governance.

It also provides Python helpers for root quality gates, security checks,
release validation, OpenAPI drift detection, and repository automation.

Use this package for CI and maintainer workflows that enforce repository
standards; it is intentionally separate from product runtime behavior.

## Why teams pick this package

- one toolkit for quality, security, release, docs, and API governance gates
- consistent local and CI behavior through shared maintainership utilities
- lower operational overhead by centralizing repetitive repo automation logic
- explicit checks that reduce release risk and configuration drift

## Typical use cases

- run and extend root quality and security gates used by all packages
- validate release readiness and metadata consistency before tagging
- build the scientific release dossier that links each workflow family to its
  benchmark, owner, tests, and explicit scientific limits
- detect OpenAPI and schema drift before publication
- automate maintainership checks for docs and repository health

## Installation

```bash
pip install -e packages/bijux-proteomics-dev
```

## Quick start

Use root `make` and `tox` commands that call this package under the hood:

```bash
make lint
make test
make test-slow
make quality
make security
```

## Public APIs

The maintainer package exposes repository-governance helpers through explicit
Python APIs:

```python
from bijux_proteomics_dev.governance.package_shape.package_tree_layout import (
    build_package_tree_layout_report,
)

report = build_package_tree_layout_report()

assert any(
    entry.distribution_name == "bijux-proteomics-core" for entry in report.packages
)
```

## Package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`
- Stable entrypoints: `quality`, `security`, `api`, `docs`, `release`, and `tools`

## Package boundaries

This package owns maintainer automation and gate implementations for the monorepo.

It does not define runtime product APIs or proteomics domain behavior.

## What this package must not do

- define scientific or runtime product semantics
- replace package-owned contracts with generic governance prose
- become a dumping ground for one-off scripts that do not express repository policy

## Contract checkpoints

- repository checks must be deterministic for the same checked-in state
- failing gates must emit actionable diagnostics instead of silent drift
- maintainer helpers may enforce package contracts, but they do not become product contracts
- new repository policy should land here before it is copied into CI scripts or ad hoc shell glue

## Choose this package when

- you need repository policy, release validation, docs integrity, or maintainer
  automation behavior
- the same check should run through root `make`, CI, and local maintainer workflows
- the concern is governance or validation rather than product semantics

## Route elsewhere when

- the change defines product runtime behavior or scientific meaning
- the helper exists only to patch one workflow with ad hoc shell glue
- the policy cannot be explained without changing an owning package contract first

## Verification route

- check `tests` for maintainer-policy, docs, release, and migration proof before
  treating a dev-package change as safe
- review `docs/SCOPE.md`, `docs/CONTRACTS.md`, `docs/ARCHITECTURE.md`, and
  `docs/TESTS.md` when governance claims are part of the change
- use `docs/index.md` plus each package `README.md`, `CHANGELOG.md`, and
  package `docs/*.md` when the change affects release policy, docs routing, or
  maintainer guidance

## Review questions

- does the change preserve repository policy, shared validation, or maintainer
  automation rather than product runtime or scientific behavior
- would workflow glue or one-off scripts otherwise become the de facto reviewer
  of release safety if this stayed outside the dev package
- can the change be justified without rewriting an owning package contract or
  boundary first

## Escalation route

- route the change to the owning product package when the proposal starts
  defining runtime behavior or scientific meaning
- stop and review `docs/SCOPE.md` and `docs/ARCHITECTURE.md` when the solution
  depends on one-off workflow glue instead of reusable maintainer policy
- escalate before release when the new rule cannot be explained without changing
  an owning package boundary or contract first

## Consumer impact signals

- expect repository-wide review when maintainer policy, release guards, or docs
  validation behavior changes because every package consumes the governance path
- treat changes that alter release gating, shared policy checks, or docs
  integrity expectations as high-impact even when package APIs stay stable
- expect a narrower release burden when the change only improves internal
  maintainer implementation without changing repository policy behavior

## Explicit non-goals

- this package does not own product semantics, scientific truth, or canonical
  runtime behavior
- this package does not replace package-local domain contracts with generic
  governance prose
- this package does not justify repository exceptions that should instead land
  as durable policy or package-owned behavior

## Source guide

- [`src/bijux_proteomics_dev/quality`](src/bijux_proteomics_dev/quality) for repository quality checks
- [`src/bijux_proteomics_dev/security`](src/bijux_proteomics_dev/security) for security gates
- [`src/bijux_proteomics_dev/governance/contracts`](src/bijux_proteomics_dev/governance/contracts) for OpenAPI and schema checks
- [`src/bijux_proteomics_dev/release`](src/bijux_proteomics_dev/release) for release support
  including `build_scientific_release_dossier()` and the checked-in
  `configs/package-governance/scientific-release-workflows.toml` manifest
- [`src/bijux_proteomics_dev/docs`](src/bijux_proteomics_dev/docs) for documentation checks
- [`src/bijux_proteomics_dev/tools`](src/bijux_proteomics_dev/tools) for maintainer utility tools

## Documentation

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Package guide](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/)
- [Scope and non-goals](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/scope-and-non-goals/)
- [Module map](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/module-map/)
- [Quality gates](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/quality-gates/)
- [Release support](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/release-support/)
- [Changelog](CHANGELOG.md)
