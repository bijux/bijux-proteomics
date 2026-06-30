---
title: Public Artifact Role Matrix
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Public Artifact Role Matrix

This page records why each shipped public artifact still exists and which stronger or weaker artifact sits beside it.

The role matrix matters because the repository now has multiple proof surfaces
for the same workflow families. Without a stronger/weaker map, the docs can
accidentally sound repetitive or inflated even when the underlying evidence is
real and distinct.

## How To Read The Matrix

- `weaker artifact` means a narrower or less decisive surface still worth
  keeping for a different reader or decision step
- `stronger artifact` means a harder challenge route or more decisive proof
  surface for the same workflow-family question
- if both columns are empty, the artifact is already suspicious and should be
  reviewed for removal or replacement

| artifact id | audience | decision role | question answered | weaker artifact | stronger artifact |
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

The role matrix exists so new public artifacts must justify a distinct decision role instead of piling up as adjacent trust-shaped noise.

## Why This Is A Quality Surface

- it prevents trust pages, rerun dossiers, and review kits from drifting into
  near-duplicates
- it keeps stronger scrutiny routes visible without erasing narrower reader
  routes
- it forces the repository to explain artifact sprawl in durable review terms

## Rule

- a new public artifact must either replace a weaker artifact or justify a distinct decision role
- workflow-family artifacts must declare the stronger or weaker surface beside them so adjacent trust pages do not drift into duplication
- current governed public artifact budget: `20`
