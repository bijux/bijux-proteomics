---
title: Quality
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Quality

This section explains how `bijux-proteomics-intelligence` earns trust after a real change: which tests defend ranking and evaluator behavior, which risks stay open, and what reviewers should still doubt.

Recommendation logic can look convincing while being wrong in subtle ways. These pages should make the proof burden explicit so a green check on one narrow path does not get mistaken for evidence that candidate selection, explanation outputs, and design-loop controls are all still sound.

## Visual Summary

```mermaid
flowchart LR
    change["change under review<br/>ranking, evaluator, or output drift"]
    lifecycle["candidate lifecycle and ranking tests"]
    scenarios["scenario evaluator and report checks"]
    guardrails["design-loop and compatibility guardrails"]
    page["Quality landing page<br/>proof, limits, and review pressure"]
    tests["tests and invariants"]
    review["review and validation"]
    limits["known limits and risks"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    change --> page
    lifecycle --> page
    scenarios --> page
    guardrails --> page
    page --> tests
    page --> review
    page --> limits
    class page page;
    class change action;
    class lifecycle,scenarios,guardrails positive;
    class tests,review,limits anchor;
```

## Pages in This Section

- [Test Strategy](test-strategy.md)
- [Invariants](invariants.md)
- [Review Checklist](review-checklist.md)
- [Documentation Standards](documentation-standards.md)
- [Definition of Done](definition-of-done.md)
- [Dependency Governance](dependency-governance.md)
- [Change Validation](change-validation.md)
- [Known Limitations](known-limitations.md)
- [Risk Register](risk-register.md)

## Start Here

Read this section when the central question is not what the package claims to do, but what evidence makes that claim believable. `bijux-proteomics-intelligence` sits close to recommendation and decision surfaces, so the quality bar has to cover behavioral drift, not just import stability.

## Read Across the Package

- [Foundation](../foundation/index.md) when you need the package boundary and ownership story first
- [Architecture](../architecture/index.md) when the question becomes structural, modular, or execution-oriented
- [Interfaces](../interfaces/index.md) when the question becomes caller-facing, schema-facing, or contract-facing
- [Operations](../operations/index.md) when the question becomes procedural, environmental, diagnostic, or release-oriented

## Concrete Anchors

- `packages/bijux-proteomics-intelligence/tests/test_candidate_lifecycle.py` for state-transition and lifecycle guarantees
- `packages/bijux-proteomics-intelligence/tests/test_candidate_ranking.py` for ranking behavior and ordering pressure
- `packages/bijux-proteomics-intelligence/tests/test_scenario_evaluators.py` and `tests/test_design_loop_surface.py` for evaluator and loop-level proof
- `packages/bijux-proteomics-intelligence/tests/test_legacy_domain_surface.py` and `tests/test_sequence_structure_forwarding.py` for compatibility guardrails

## Use This Page When

- you are reviewing tests, invariants, limitations, and decision-quality risks
- you need evidence that recommendation behavior and output surfaces are actually defended
- you are deciding whether a change is done or only implemented

## Do Not Use This Section When

- you are still trying to understand package scope or ownership
- you need the structural map of candidates, policies, evaluators, reports, and loop control
- you need the practical workflow for running or releasing the package

## When To Leave This Section

Move to [Interfaces](../interfaces/index.md) when a proof question turns out to be a contract question about an import, artifact, or configuration shape. Move to [Operations](../operations/index.md) when you know what has to be proven and now need the repeatable procedure for proving it. Move to [Architecture](../architecture/index.md) when a failing quality story reveals a deeper split-of-responsibility problem inside the package.

## Reader Takeaway

Treat this section as the proof map for `bijux-proteomics-intelligence`. If a change touches ranking, evaluator behavior, explanation outputs, or compatibility forwarding, the work is not done until the relevant tests, review criteria, and visible limits still support the claim.
