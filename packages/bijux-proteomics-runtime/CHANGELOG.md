# Changelog

All notable changes for `bijux-proteomics-runtime` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added the canonical runtime package with typed CLI and API entrypoints,
  provider binding, run management, reviewable sequence and import paths,
  collaborator handoff archives, artifact checkpoint, rehydration, diff, and
  comparison surfaces, and deterministic replay contracts.
- Added typed workflow DAG, step-type, semantic-cache, partial-rerun, and
  workflow-failure contracts so runtime planning and stage reuse stay
  machine-readable and auditable.
- Added advanced DIA-NN public workflows for dry-run planning, deterministic
  run identity, resumable stage reuse, archived result bundles, runtime smoke
  bundles, and architecture-demo routes.

### Changed

- Rebuilt runtime around explicit `api`, `providers`, `runs`, `workflows`,
  `state`, `support`, and `governance` owner families and tightened
  dependency-light imports plus optional provider guards.
- Expanded executable README and package docs for runtime APIs, advanced
  DIA-NN tutorials, archived workflow ownership, and black-box rerun trust
  surfaces.
- Aligned dependency floors and fallback version with the `0.3.8` release
  line.

### Fixed

- Hardened guarded route methods, multiplex import handling, bytecode hygiene,
  security-sensitive asserts, and the governed local-folding dependency
  policy.
