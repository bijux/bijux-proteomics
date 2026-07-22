---
title: Quality Gates
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-07-21
---

# Quality gates

Quality gates turn repository invariants into deterministic pass or fail
decisions. Each failure names the violated contract and enough evidence to route
the correction to its owner. Gates do not rewrite source, relax policy, or hide
known debt to manufacture a green result.

## Gate families

| Family | Examples | Protects |
| --- | --- | --- |
| package quality | Vulture, Deptry, Mypy, Interrogate | dead code, dependency hygiene, typing, documentation coverage |
| documentation | links, consistency, architecture docs, design debt | published navigation and source-backed claims |
| architecture | runtime boundaries, circular imports, canonical package tree | package ownership and dependency direction |
| contracts | API freeze, OpenAPI drift, public API types | machine-readable and import-facing compatibility |
| artifacts | root hygiene, file ownership, generated markers | governed storage and reproducible outputs |
| release | migration ledger, collection gate, release preflight | coordinated package-family readiness |
| security | Bandit, dependency audit, allowlist | source and dependency security posture |

```mermaid
flowchart LR
    focused["focused package or policy gate"]
    family["repository family gate"]
    composite["quality · security · test · docs · api"]
    preflight["release preflight"]
    focused --> family --> composite --> preflight
```

## Run from narrow to broad

During development, run the closest package or named policy target. Before
handoff, run the public repository gate that includes it. Examples:

```bash
make quality PACKAGE=bijux-proteomics-knowledge
make quality-docs-links
make quality-artifact-governance
make quality-runtime-migration-validation
make quality
```

The root `quality` dispatcher runs package quality and then repository-level
post-gates. `make check` is broader: it includes lock, lint, collection, tests,
quality, security, docs, APIs, builds, and SBOMs.

| Gate scope | Appropriate use | Insufficient use |
| --- | --- | --- |
| helper or policy test | develop one validator and exercise pass/failure behavior | claim the affected package is ready |
| package gate | close behavior and structure for one owned package | claim cross-package or publication safety |
| repository family gate | check one shared contract across packages | replace scientific, security, or release families not included |
| composite gate | establish the named collection for one revision | infer that an unlisted gate ran or that public claims are true |
| release preflight | assemble the required publication evidence | authorize publication without candidate identity and reviewer decision |

## Failure contract

A gate failure reports the failing object, policy, and remediation direction.
Composite dispatch continues across packages where possible and reports the
complete failing package set. A check that cannot run because its environment
or governed input is missing fails explicitly rather than treating absence as
success.

Known failures remain failures. Record them in the handoff with exact paths and
diagnostics; do not add ignores, broaden exclusions, lower thresholds, or skip
the gate unless the underlying policy intentionally changes through review.

Failures use different dispositions and must remain distinguishable:

- **violation** — the checked object contradicts the governed rule;
- **stale evidence** — a generated or frozen contract no longer matches its
  source inputs;
- **blocked execution** — the gate could not evaluate because a required
  environment or governed input is absent;
- **validator defect** — the gate itself crashes or produces an invalid
  verdict;
- **intentional contract movement** — the old contract fails and requires an
  explicit reviewed replacement, migration, and regenerated evidence.

Only the last disposition can justify changing the governing baseline, and it
still remains a failure until the replacement contract is reviewed and all
affected consumers pass.

## Adding a gate

Add a gate only when the invariant is durable, automatable, and owned. Implement
the narrow helper, test pass and failure cases, expose a named Make target, wire
it into the appropriate composite layer, and document its inputs and verdict.
Avoid duplicating a rule already enforced by package tooling or shared
standards.

The registration record for a new gate must name its owner, inputs, protected
invariant, deterministic verdict, failure format, output location, composite
membership, and removal condition. A gate without an owner or remediation path
creates noise rather than governance.
