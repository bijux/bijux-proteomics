---
title: Quality
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Quality

This section explains how `agentic-proteins` earns trust as a compatibility
bridge: which forwarding proofs matter, which migration risks stay visible, and
what done should mean before a preserved legacy surface is changed or removed.

These pages explain the proof story for the bridge package. They make
trust, skepticism, and retirement pressure visible enough that passing checks
do not get mistaken for sufficient migration evidence.

This section keeps readers with a narrow quality lens: a compatibility
package is trustworthy when it forwards deliberately, fails loudly when the
bridge breaks, and does not hide retirement debt behind green checks alone.

## Pages In This Section

- [Test Strategy](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/test-strategy/)
- [Invariants](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/invariants/)
- [Review Checklist](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/review-checklist/)
- [Documentation Standards](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/documentation-standards/)
- [Definition of Done](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/definition-of-done/)
- [Dependency Governance](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/dependency-governance/)
- [Change Validation](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/change-validation/)
- [Known Limitations](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/known-limitations/)
- [Risk Register](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/risk-register/)

## Open This Section When

- you are reviewing forwarding tests, alias coverage, compatibility limits, or
  retirement risk
- you need evidence that a preserved legacy surface is still defended honestly
- you are deciding whether bridge work is truly done instead of merely passing
  a narrow check

## Open Another Section When

- the real proof question belongs to the canonical runtime package
- you are evaluating new product quality rather than legacy-surface safety
- the issue is architectural or caller-facing rather than proof-facing

## Bottom Line

Quality here is about safe preservation and safe exit. If the bridge still
ships, readers should be able to see why it is trustworthy today and what proof
would justify retiring it tomorrow.

## Read Across the Package

- [Foundation](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/) when you need the package boundary and ownership story first
- [Architecture](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/) when the question becomes structural, modular, or execution-oriented
- [Interfaces](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/) when the question becomes caller-facing, schema-facing, or contract-facing
- [Operations](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/) when the question becomes procedural, environmental, diagnostic, or release-oriented

## Concrete Anchors

- packages/agentic-proteins/tests/api and tests/integration for interface and contract behavior
- packages/agentic-proteins/tests/e2e and tests/regression for end-to-end and drift protection
- README.md

## Open This Page When

- you are reviewing tests, invariants, limitations, or ongoing risks
- you need evidence that the documented contract is actually defended
- you are deciding whether a change is truly done rather than merely implemented

## Decision Rule

Open this section to decide whether `agentic-proteins` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

## What You Can Resolve Here

- what currently proves the `agentic-proteins` contract instead of merely describing it
- which risks, limits, and assumptions still need explicit skepticism
- what a reviewer should be able to say before accepting a change as done

## Review Focus

- compare the documented proof story with the actual test layout and release posture
- look for limitations or risks that should have moved with recent behavior changes
- verify that the claimed done-ness standard still reflects real validation practice

## Limits

Tests, checks, and review practice remain the proof for this package. If they drift, this page is wrong.

## Read Next

- open foundation when the risk appears to be boundary confusion rather than missing tests
- open architecture when the proof gap points to structural drift
- open interfaces or operations when the proof question is really about a contract or workflow

