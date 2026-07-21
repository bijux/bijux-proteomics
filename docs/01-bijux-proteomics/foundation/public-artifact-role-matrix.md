---
title: Public Artifact Role Matrix
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-21
---

# Public Artifact Role Matrix

Artifacts that discuss the same workflow can carry different authority. This matrix distinguishes navigation from proof, primary evidence from derived views, and a bounded positive result from challenge evidence that can overturn it.

A weaker artifact answers a narrower question or derives from evidence elsewhere. A stronger artifact is the more direct or demanding authority for the claim under review.

## Authority Order

```mermaid
flowchart LR
    guide["guide or index"] --> summary["generated summary"]
    summary --> record["versioned evidence record"]
    record --> challenge["independent challenge result"]
    challenge --> refusal["release acceptance or refusal"]
```

Authority is question-specific. A benchmark manifest is stronger than a prose summary for input identity, while a Runtime run bundle is stronger for what executed. Neither can answer the other question by itself.

## Artifact Roles

| Artifact id | Audience | Decision role | Question answered | Weaker artifact | Stronger artifact |
| --- | --- | --- | --- | --- | --- |
| `artifact-index:release-candidate` | `scientist` | `repository-release-boundary` | Which workflow families can the repository defend today? | `artifact-index:elite-readiness-scorecard` | `artifact-index:hostile-review-kit` |
| `artifact-index:elite-readiness-scorecard` | `maintainer` | `repository-language-ceiling` | How far may repository-wide language go today? | - | `artifact-index:release-candidate` |
| `artifact-index:hostile-review-kit` | `skeptical outsider` | `repository-challenge-route` | What is the shortest whole-repository challenge route? | `artifact-index:release-candidate` | - |
| `artifact-index:why-not-ready` | `reviewer` | `repository-blocker-ledger` | Which blocked release bars still fail right now? | `artifact-index:elite-readiness-scorecard` | `artifact-index:what-makes-ready` |
| `artifact-index:what-makes-ready` | `maintainer` | `repository-closing-conditions` | What concrete evidence would move the release boundary next? | `artifact-index:why-not-ready` | - |
| `artifact-index:dda:trust-page` | `scientist` | `workflow-justification` | Why does dda still earn bounded outsider-auditable language today? | `artifact-index:release-candidate` | `artifact-index:dda:external-review-kit` |
| `artifact-index:dda:independent-rerun` | `operator` | `workflow-rerun-challenge` | Can dda survive a second checked rerun challenge? | `artifact-index:dda:trust-page` | `artifact-index:dda:external-review-kit` |
| `artifact-index:dda:external-review-kit` | `skeptical outsider` | `workflow-outsider-challenge` | What should an outsider open to challenge the dda sentence? | `artifact-index:dda:independent-rerun` | - |
| `artifact-index:dia:trust-page` | `scientist` | `workflow-justification` | Why does dia still earn bounded outsider-auditable language today? | `artifact-index:release-candidate` | `artifact-index:dia:external-review-kit` |
| `artifact-index:dia:independent-rerun` | `operator` | `workflow-rerun-challenge` | Can dia survive a second checked rerun challenge? | `artifact-index:dia:trust-page` | `artifact-index:dia:external-review-kit` |
| `artifact-index:dia:external-review-kit` | `skeptical outsider` | `workflow-outsider-challenge` | What should an outsider open to challenge the dia sentence? | `artifact-index:dia:independent-rerun` | - |
| `artifact-index:lfq:trust-page` | `scientist` | `workflow-justification` | Why does lfq still earn bounded outsider-auditable language today? | `artifact-index:release-candidate` | `artifact-index:lfq:external-review-kit` |
| `artifact-index:lfq:independent-rerun` | `operator` | `workflow-rerun-challenge` | Can lfq survive a second checked rerun challenge? | `artifact-index:lfq:trust-page` | `artifact-index:lfq:external-review-kit` |
| `artifact-index:lfq:external-review-kit` | `skeptical outsider` | `workflow-outsider-challenge` | What should an outsider open to challenge the lfq sentence? | `artifact-index:lfq:independent-rerun` | - |
| `artifact-index:ptm:trust-page` | `scientist` | `workflow-justification` | Why does ptm still earn bounded outsider-auditable language today? | `artifact-index:release-candidate` | `artifact-index:ptm:external-review-kit` |
| `artifact-index:ptm:independent-rerun` | `operator` | `workflow-rerun-challenge` | Can ptm survive a second checked rerun challenge? | `artifact-index:ptm:trust-page` | `artifact-index:ptm:external-review-kit` |
| `artifact-index:ptm:external-review-kit` | `skeptical outsider` | `workflow-outsider-challenge` | What should an outsider open to challenge the ptm sentence? | `artifact-index:ptm:independent-rerun` | - |
| `artifact-index:targeted:trust-page` | `scientist` | `workflow-justification` | Why does targeted still earn bounded outsider-auditable language today? | `artifact-index:release-candidate` | `artifact-index:targeted:external-review-kit` |
| `artifact-index:targeted:independent-rerun` | `operator` | `workflow-rerun-challenge` | Can targeted survive a second checked rerun challenge? | `artifact-index:targeted:trust-page` | `artifact-index:targeted:external-review-kit` |
| `artifact-index:targeted:external-review-kit` | `skeptical outsider` | `workflow-outsider-challenge` | What should an outsider open to challenge the targeted sentence? | `artifact-index:targeted:independent-rerun` | - |

## Coexistence Rules

The role matrix exists so new public artifacts must justify a distinct decision role instead of piling up as adjacent trust-shaped noise.

Two public artifacts may coexist when:

- they have different owner packages or authority questions;
- one is a stable derived view with a freshness check and resolvable source;
- one preserves historical or compatibility evidence required for replay;
- one applies independent pressure absent from the primary artifact.

Consolidate or remove an artifact when:

- it repeats another artifact's conclusion without adding evidence or a reader route;
- its owner, generator, source identity, or freshness check is unknown;
- readers can mistake it for a stronger authority surface;
- no compatibility contract requires its continued publication.

When artifacts disagree, open their source identities, owner contracts, and validators. Narrow the claim until the conflict is resolved; the preferred conclusion does not select the winner.

The current governed public artifact budget is `20`.
