---
title: Public Artifact Role Matrix
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Public Artifact Role Matrix

This page records why public proof surfaces that look adjacent still both
exist, and which one is stronger when they answer related questions.

The point is not cataloging for its own sake. The point is to stop the docs
tree from accumulating several trust-shaped pages that all feel similar but do
not clearly justify their coexistence.

## How To Read The Matrix

- `weaker surface` means a narrower or less decisive page that still helps a
  different reader or decision step
- `stronger surface` means the harder challenge route for the same question
- if an entry cannot name either side, it should be reviewed for removal or
  consolidation

## Repository-Level Roles

| surface | role | weaker surface | stronger surface |
| --- | --- | --- | --- |
| [Flagship Release Candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/) | strongest current release sentence | [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/) when the question is only ceiling language | [Hostile Review Kit](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/hostile-review-kit/) when the question is the hardest outsider challenge route |
| [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/) | honesty boundary and release-language brake | none | [Flagship Release Candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/) when the question is the current positive sentence |
| [Hostile Review Kit](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/hostile-review-kit/) | strongest whole-repository challenge route | [Flagship Release Candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/) | none |
| [What Would Make This Repository Ready](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-would-make-this-repository-ready/) | closing-condition surface for wider language | [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/) | none |

## Workflow-Family Roles

For each outsider-facing flagship family:

- the trust page is weaker than the external review kit because it explains the
  sentence rather than challenging it as hard as possible
- the independent rerun dossier is weaker than the external review kit because
  it isolates the replay and rerun challenge instead of packaging the full
  benchmark-to-consequence route
- the external review kit is the strongest outsider-facing family artifact
  because it packages the distinct challenge surfaces together

This role pattern applies to `dda`, `dia`, `lfq`, `ptm`, and `targeted`.

## Why This Is A Quality Surface

- it forces new public artifacts to justify a distinct decision role
- it makes weaker-but-still-useful surfaces explicit instead of accidental
- it gives maintainers a durable removal rule when the tree starts to sprawl

## Rule

A new public artifact should do one of two things:

- replace a weaker surface
- justify a distinct stronger or weaker role beside an existing surface

If it does neither, it should not remain in the public artifact set.

## Boundary

This page explains coexistence and replacement pressure. It should not become
a second index once the stronger opening order is already clear.
