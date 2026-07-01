---
title: Public Language Glossary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Public Language Glossary

This page governs the release-facing vocabulary that root docs, package docs, and public route contracts may use without drifting back into repository lore.

The glossary matters more now because the repository has stronger real product
depth than it did at `v0.3.7`. Once benchmark, runtime, grounding,
recommendation, and consequence routes all become more substantial, the real
risk is that public wording outruns the weakest hop and makes the whole system
sound cleaner or broader than the proof chain actually allows.

## Allowed Terms

| term | use it as | allowed surfaces | why it stays |
| --- | --- | --- | --- |
| `outsider-auditable` | `outsider-auditable` | `README.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`, `docs/01-bijux-proteomics/foundation/workflow-claim-limits.md` | Use this only for workflow families whose current package, rerun, and review surfaces survive skeptical opening order without maintainer narration. |
| `internal-support-only` | `internal-support-only` | `README.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`, `docs/01-bijux-proteomics/foundation/workflow-claim-limits.md`, `docs/01-bijux-proteomics/foundation/why-multiplex-stops-at-internal-support.md` | Use this for workflow families with real substance that still do not earn outsider-facing release language. |
| `independent rerun dossier` | `independent rerun dossier` | `docs/01-bijux-proteomics/foundation/independent-rerun-dossiers.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md` | This names a distinct reviewer-facing artifact that tests whether one workflow sentence survives a second challenge lane. |
| `external review kit` | `external review kit` | `docs/01-bijux-proteomics/foundation/external-review-kits.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md` | This names the shortest outsider opening order through benchmark, rerun, and recommendation evidence for one workflow family. |
| `decision brief` | `decision brief` | `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/routes/decision_briefs.py` | This remains a stable route-contract term for package-owned packet creation, lookup, diff, and export operations. |

## Why These Terms Need Tight Control

- one relaxed release word can erase the difference between grounded evidence
  and recommendation posture
- one vague trust phrase can hide whether a workflow family is bounded,
  review-grade, or internal-support-only
- one legacy campaign label can make the repository sound broader than the
  current family packets justify

## Retired Terms

| retired phrase | use instead | why it was retired |
| --- | --- | --- |
| `authority boundary` | `claim limits or internal-support limit` | This phrase hid the real reader question. Public docs should now say what claims are supported, blocked, or refused. |
| `workflow authority matrix` | `workflow claim limits` | The page no longer exists to project authority. It exists to state current claim limits per workflow family. |
| `canonical workflow` | `what one workflow family supports today` | The old label sounded broader and more final than the one bounded workflow sentence the repository can currently defend. |
| `reviewable-proteomics` | `flagship workflow chain or bounded workflow family` | This was an internal campaign label, not a durable public product name or workflow concept. |
| `multiplex authority boundary` | `why multiplex stops at internal support` | Readers need a direct answer about multiplex limits, not a repository-internal framing term. |

## Enforcement

- `validate_public_language()` rejects retired phrases in root docs, package READMEs, foundation docs, and release-support surfaces.
- `workflow_public_scrutiny.py` and `final_preflight.py` both depend on this glossary before stronger release wording may pass.
- New public terms belong here before they spread across repository-owned docs or public route contracts.

## Strongest Reader Use

- open this page when a root doc, README, trust page, or release note sounds
  stronger than the current readiness and claim-limit surfaces
- treat retired phrases as a warning that the wording is trying to compress a
  real boundary back into repository shorthand
