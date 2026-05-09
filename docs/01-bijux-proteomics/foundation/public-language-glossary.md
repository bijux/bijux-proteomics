---
title: Public Language Glossary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Public Language Glossary

This page governs the release-facing vocabulary that root docs, package docs, and public route contracts may use without drifting back into repository lore.

## Allowed Terms

| term | use it as | allowed surfaces | why it stays |
| --- | --- | --- | --- |
| `outsider-auditable` | `outsider-auditable` | `README.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`, `docs/01-bijux-proteomics/foundation/workflow-claim-limits.md` | Use this only for workflow families whose current package, rerun, and review surfaces survive skeptical opening order without maintainer narration. |
| `internal-support-only` | `internal-support-only` | `README.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`, `docs/01-bijux-proteomics/foundation/workflow-claim-limits.md`, `docs/01-bijux-proteomics/foundation/why-multiplex-stops-at-internal-support.md` | Use this for workflow families with real substance that still do not earn outsider-facing release language. |
| `independent rerun dossier` | `independent rerun dossier` | `docs/01-bijux-proteomics/foundation/independent-rerun-dossiers.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md` | This names a distinct reviewer-facing artifact that tests whether one workflow sentence survives a second challenge lane. |
| `external review kit` | `external review kit` | `docs/01-bijux-proteomics/foundation/external-review-kits.md`, `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md` | This names the shortest outsider opening order through benchmark, rerun, and recommendation evidence for one workflow family. |
| `review packet` | `review packet` | `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/routes/review_packets.py` | This remains a stable route-contract term for package-owned packet creation, lookup, diff, and export operations. |

## Retired Terms

| retired phrase | use instead | why it was retired |
| --- | --- | --- |
| `authority boundary` | `claim limits or internal-support limit` | This phrase hid the real reader question. Public docs should now say what claims are supported, blocked, or refused. |
| `workflow authority matrix` | `workflow claim limits` | The page no longer exists to project authority. It exists to state current claim limits per workflow family. |
| `canonical workflow proof` | `what one workflow family supports today` | The old label sounded broader and more final than the one bounded workflow sentence the repository can currently defend. |
| `multiplex authority boundary` | `why multiplex stops at internal support` | Readers need a direct answer about multiplex limits, not a repository-internal framing term. |

## Enforcement

- `validate_public_language()` rejects retired phrases in root docs, package READMEs, foundation docs, and release-support surfaces.
- `workflow_public_scrutiny.py` and `final_preflight.py` both depend on this glossary before stronger release wording may pass.
- New public terms belong here before they spread across repository-owned docs or public route contracts.
