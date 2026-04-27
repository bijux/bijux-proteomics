# bijux-proteomics-dev

`bijux-proteomics-dev` is the maintainer package for repository policy,
quality gates, release validation, docs checks, and operational helper tools in
`bijux-proteomics`.

## Package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`
- Repository: `bijux/bijux-proteomics`
- Documentation route: `08-bijux-proteomics-maintain/bijux-proteomics-dev/`

## Package role

Use this package when work belongs to repository maintenance rather than product
runtime or scientific domain behavior.

It owns:

- quality and security gate implementations
- release-readiness and metadata validation
- docs consistency and publication checks
- maintainer-only operational helper tooling

## Boundary reminders

- product runtime ownership stays in `bijux-proteomics-runtime`
- scientific meaning stays in the lower `bijux-proteomics-*` packages
- CI and root automation should call this package instead of embedding policy in
  workflow-local shell glue

## Key maintainer entrypoints

- `docs/SCOPE.md` for maintainer-package ownership and non-goals
- `docs/ARCHITECTURE.md` for maintainer-package topology and dependency rules
- `docs/CONTRACTS.md` for stable maintainer contract surfaces
- `docs/TESTS.md` for the expected test strata behind repository policy changes

## Release policy entrypoints

- publishable package `docs/maintainer/pypi.md` files for package-specific
  release contract, validation focus, and publication checkpoints
- `src/bijux_proteomics_dev/release` for release-readiness validation logic
- `test_release_workflows.py`, `test_packaging_contract.py`, and related docs
  contract tests for the executable proof behind release policy

## Release escalation surfaces

- package `docs/maintainer/pypi.md` files when a maintainer cannot justify a
  release as safe within the current package boundary
- `docs/TESTS.md` and release-policy tests when workflow wiring is green but
  the claimed proof surface is still ambiguous
- `src/bijux_proteomics_dev/release` when release-readiness rules need a
  durable policy change instead of a workflow-local exception

## Release review questions

- does the proposed release claim belong to package-owned release policy rather
  than to runtime or scientific package behavior
- would workflow YAML, shell glue, or one-off scripts otherwise become the
  de facto reviewer of release safety
- can the release still be justified without claiming product runtime execution
  or scientific domain truth as maintainer-owned logic

## Source guide

- `src/bijux_proteomics_dev/quality` for repository quality and migration checks
- `src/bijux_proteomics_dev/security` for security and dependency policy gates
- `src/bijux_proteomics_dev/api` for OpenAPI drift and freeze checks
- `src/bijux_proteomics_dev/release` for release-readiness validation
- `src/bijux_proteomics_dev/docs` for documentation integrity and publication checks
- `src/bijux_proteomics_dev/tools` for maintainers-only operational helpers

## Downstream expectation

When repository policy changes, the durable implementation should land here and
be called from `make`, CI, or release workflows, rather than being duplicated
across ad hoc scripts.
