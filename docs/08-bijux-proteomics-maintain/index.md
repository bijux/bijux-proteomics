---
title: Maintainer Handbook
audience: maintainer
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-07-21
---

# Maintainer handbook

Repository maintenance keeps fifteen published distributions, their API
contracts, documentation, release artifacts, and scientific boundaries
coherent. Package-local checks establish local behavior; repository gates
establish whether that behavior still composes safely.

## Verification architecture

```mermaid
flowchart LR
    change["source, docs, schema, or dependency change"]
    make["Make target\nstable operator entry point"]
    dev["bijux-proteomics-dev\npolicy and validation code"]
    checks["tests · lint · typing · API · security · docs · architecture"]
    ci["GitHub workflows\nclean-environment verification"]
    release["PyPI · GHCR · GitHub Release · docs"]
    change --> make --> dev --> checks --> ci --> release
```

The same named Make targets are used locally and in automation. Generated API,
schema, governance, and documentation evidence is checked for drift rather than
treated as an informal review aid.

## Local workflow

From the repository root:

```bash
make ensure-venv
make test
make quality
make security
make api
make docs-check
```

Use the narrowest package target during development, then run the relevant
repository gate before committing. `make check` is the full verification flow;
`make release-preflight` applies the ordered hostile-review checks required
before a release candidate.

All generated local outputs belong under `artifacts/`. Package trees contain
source, tests, governed fixtures, and release-owned assets—not transient logs,
coverage output, caches, or ad hoc run products.

## Change-to-gate map

| Changed surface | Required focus |
| --- | --- |
| Python behavior | package tests, lint, type checks, public API types |
| package imports or dependencies | lock check, circular-import checks, dependency minimization, optional-dependency guards |
| public exports | API checks, schema freeze, API lock and compatibility review |
| runtime or compatibility bridge | runtime boundaries, migration ledger, migration validation |
| docs or navigation | docs links, consistency, strict MkDocs build, docs hygiene |
| architecture or package layout | canonical package tree, orphan modules, architecture regression |
| release metadata | builds, SBOMs, badge checks, license assets, release preflight |
| security-sensitive code | static security, vulnerability gates, dependency allowlist |

## Generated evidence ownership

Generated files are governed artifacts, not convenient text snapshots. The
generator owns content and ordering; the generated path owns review and
publication. A coherent change identifies both.

```mermaid
flowchart LR
    S["source contract or policy"] --> G["named generator"]
    G --> O["governed output"]
    O --> C["check mode compares bytes"]
    C -->|match| R["review source and output"]
    C -->|drift| F["repair generator or regenerate"]
```

Hand-editing an output without updating its owner produces the same failure on
the next regeneration. Regenerating without understanding the source can hide
an unintended policy change. Review handwritten and generated diffs separately
even when correctness requires them in one commit.

## Interpret gate results

```mermaid
flowchart TD
    G["named gate"] --> R{"result"}
    R -->|pass| E["record evidence and continue"]
    R -->|fail| O{"change caused failure?"}
    O -->|yes| C["correct implementation or narrow claim"]
    O -->|no| B["record existing blocker with exact output"]
    C --> G
    B --> P["keep blocker visible in review and release posture"]
```

A pre-existing failure is still a failure. Distinguishing it from the current
change preserves scope; it does not make the repository green. Do not exclude,
mute, reclassify, or regenerate evidence merely to make a gate pass.

Verification output supports different claims:

| Evidence | Supports | Does not establish |
| --- | --- | --- |
| package unit tests | local behavior under covered cases | cross-package compatibility or scientific validity |
| type and quality gates | static contracts and repository policy | runtime success or publication readiness |
| documentation build | links, navigation, syntax, and configured rendering | truth of every scientific statement |
| migration validation | declared compatibility surfaces and equivalence checks | absence of undeclared consumers |
| release preflight | the ordered release policy at one revision | universal workflow validity |
| built-wheel installation | package contents and installability | end-to-end scientific readiness |

## Repository owners

- [`bijux-proteomics-dev`](bijux-proteomics-dev/index.md) implements quality,
  security, API, schema, documentation, governance, and release validators.
- [The Make system](makes/index.md) provides discoverable root commands and
  package dispatch without duplicating policy.
- [GitHub workflows](gh-workflows/index.md) run clean-environment verification,
  publication, and docs deployment.
- `configs/` contains tool and governed policy inputs; `apis/` contains tracked
  public-contract evidence.

## Safe change sequence

1. Identify the package owner and the public contract affected.
2. Change implementation and package-local tests together.
3. Regenerate governed outputs only through their owning command.
4. Inspect generated and handwritten diffs separately.
5. Run the narrow package checks and the repository gates implied by the
   change-to-gate map.
6. Confirm documentation describes released behavior and its limitations.
7. Build and inspect distributions when packaging or public data changes.

Detailed operational routes are available in
[maintainer safe change](bijux-proteomics-dev/maintainer-safe-change.md),
[quality gates](bijux-proteomics-dev/quality-gates.md),
[schema governance](bijux-proteomics-dev/schema-governance.md), and
[release support](bijux-proteomics-dev/release-support.md).

## Commit boundary

A commit represents one durable intent whose affected checks have a known
result. Selective staging keeps unrelated user work outside that intent.
Generated sync, handwritten behavior, and documentation can share a commit
when they are inseparable for correctness; otherwise they remain separate so a
reviewer can identify the policy source and its consequences.

## Release boundary

Releases are tag-driven and publish independently versioned distributions. A
green build is necessary but does not prove scientific readiness. Release
review also checks workflow-family evidence, runtime replay, grounding,
recommendation posture, lab consequence, package compatibility, and the
accuracy of public claims.

Release evidence is revision-specific. Preserve the exact source identity,
environment, commands, and failure output needed to review or repeat it.
