# bijux-proteomics-dev

`bijux-proteomics-dev` is the maintenance toolkit for this monorepo. It
provides Python helpers for root quality gates, security checks, release
validation, OpenAPI drift detection, and repository automation.

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
make quality
make security
```

## Package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`
- Stable entrypoints: `quality`, `security`, `api`, `docs`, `release`, and `tools`

## Package boundaries

This package owns maintainer automation and gate implementations for the monorepo.

It does not define runtime product APIs or proteomics domain behavior.

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

## Source guide

- [`src/bijux_proteomics_dev/quality`](src/bijux_proteomics_dev/quality) for repository quality checks
- [`src/bijux_proteomics_dev/security`](src/bijux_proteomics_dev/security) for security gates
- [`src/bijux_proteomics_dev/api`](src/bijux_proteomics_dev/api) for OpenAPI and schema checks
- [`src/bijux_proteomics_dev/release`](src/bijux_proteomics_dev/release) for release support
- [`src/bijux_proteomics_dev/docs`](src/bijux_proteomics_dev/docs) for documentation checks
- [`src/bijux_proteomics_dev/tools`](src/bijux_proteomics_dev/tools) for maintainer utility tools

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/)
- [Scope and non-goals](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/scope-and-non-goals/)
- [Module map](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/module-map/)
- [Quality gates](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/quality-gates/)
- [Release support](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/release-support/)
- [Changelog](CHANGELOG.md)
