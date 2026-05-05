---
title: Package Substance
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-dev
last_reviewed: 2026-05-05
---

# package substance

This report makes package-boundary substance explicit. The five real product packages must carry enough owned logic to justify their boundaries, the shared kernel must stay narrow and reusable, the compatibility bridge must stay wrapper-only, and the maintainer package must remain a real repository-health surface instead of a token directory.

## Boundary Roles

- canonical products: 5
- shared kernels: 1
- compatibility bridges: 1
- maintainer support packages: 1

## Current Package Counts

- `agentic-proteins`: role=compatibility_bridge, owned_logic=0, wrappers=147, thin=0, ready=yes
- `bijux-proteomics-core`: role=canonical_product, owned_logic=89, wrappers=0, thin=25, ready=yes
- `bijux-proteomics-dev`: role=maintainer_support, owned_logic=53, wrappers=0, thin=8, ready=yes
- `bijux-proteomics-foundation`: role=shared_kernel, owned_logic=21, wrappers=7, thin=1, ready=yes
- `bijux-proteomics-intelligence`: role=canonical_product, owned_logic=11, wrappers=0, thin=1, ready=yes
- `bijux-proteomics-knowledge`: role=canonical_product, owned_logic=20, wrappers=0, thin=2, ready=yes
- `bijux-proteomics-lab`: role=canonical_product, owned_logic=15, wrappers=0, thin=1, ready=yes
- `bijux-proteomics-runtime`: role=canonical_product, owned_logic=111, wrappers=0, thin=27, ready=yes

## Release Rule

- the five real product packages must keep enough owned logic to justify separate release identities
- the shared kernel must stay narrow, reusable, and free of presentation or workflow ownership drift
- the compatibility bridge is allowed to be thin only because it is explicitly a wrapper-only bridge
- package-boundary thinness is release-blocking when it hides unresolved SSOT ownership
- current package substance issues: 0

## First Proof Check

- `docs/08-bijux-proteomics-maintain/bijux-proteomics-dev/package-substance.csv`
- `docs/08-bijux-proteomics-maintain/bijux-proteomics-dev/package-substance.md`
- `packages/bijux-proteomics-dev/tests/test_package_substance.py`
