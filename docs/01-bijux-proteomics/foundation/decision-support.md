---
title: Decision Support
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Decision Support

This route exists for the question after benchmark and runtime evidence: what
should a skeptical reviewer or decision-maker believe now, and which owner
surface justifies that belief.

The point of this route is not generic governance. It is the product surface
where grounded evidence, contradiction handling, analytical judgment, and lab
burden are forced onto one honest chain. If that chain is weak, the public
language must narrow even when the code or benchmark count looks impressive.

## How To Use This Route

- start with one workflow family instead of trying to decide whether the whole
  repository is trustworthy at once
- move in order from grounded evidence to recommendation posture to downstream
  consequence instead of reading those surfaces as unrelated package summaries
- treat the weakest honest sentence as the real product surface, even when one
  upstream benchmark or runtime artifact looks stronger in isolation
- stop at the owner surface that can still defend the sentence without hand
  waving

## What This Route Actually Governs

- grounded evidence and contradiction state from `bijux-proteomics-knowledge`
- recommendation posture, ranking, downgrade, and refusal from
  `bijux-proteomics-intelligence`
- downstream operator burden, control demand, and requested-versus-observed
  follow-up from `bijux-proteomics-lab`
- release wording that must stay weaker whenever those owner surfaces disagree
  or remain advisory

## One Honest Decision Chain

- benchmark and runtime surfaces establish what happened and what can be
  replayed
- knowledge establishes what the repository can ground and where contradiction
  still survives
- intelligence establishes how strong the recommendation may sound after that
  pressure
- lab establishes whether the requested follow-up still deserves real-world
  burden once the analytical story is known

## Start Here

- Open [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
  when the disagreement is already about the full chain from contradiction
  pressure to recommendation posture to assay burden.
- Open [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/)
  when the next reviewer question is which evidence axis or observed outcome
  actually moved the call.
- Open [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
  when the disagreement starts from grounded claim support.
- Open [Workflow Literature Audits](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-literature-audits/)
  when the disagreement starts from external scientific pressure.
- Open [Workflow Recommendation Confidence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence/)
  when the disagreement is about how strong the current recommendation may be.
- Open [Public Artifact Index](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-index/)
  and [Public Artifact Role Matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-role-matrix/)
  when the disagreement is about which public surface still earns space.

## Strongest Questions To Ask

- Is the current recommendation grounded in cited knowledge, or only supported
  by workflow-local evidence?
- Did a runtime replay, comparator result, or observed follow-up actually
  change the recommendation, or did only the prose change?
- Is the current call blocked by contradiction, downgrade pressure, or
  downstream assay burden even though one benchmark package looks strong?
- Which artifact should a skeptical reader open first to see the strongest
  evidence for the current sentence?

## Decision Questions

- Which workflow family still survives as one combined consequence chain instead
  of three separate package stories?
- Which evidence axis or observed follow-up outcome actually changed the current
  recommendation?
- Which evidence is grounded but still contradicted?
- Which family sentence is benchmark-backed yet still narrowed by runtime or
  consequence pressure?
- Which public artifact is stronger than its neighbor, and why does the weaker
  one still remain?
- Which release phrase is still blocked even if the docs explanation sounds
  persuasive?

## What This Route Refuses

- it refuses to let runtime realism substitute for grounded belief
- it refuses to let grounded evidence substitute for recommendation posture
- it refuses to let recommendation posture substitute for downstream assay
  worth
- it refuses to let cleaner prose outrun the weakest live owner surface

## Interpretation Rule

If knowledge, intelligence, and lab do not all support the same stronger
sentence, the weaker shared sentence wins. The decision route exists to make
that downgrade visible instead of letting package-local confidence outrun the
combined consequence chain.

## Adjacent Routes

- Open [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  when you need the family comparison before choosing a knowledge or
  intelligence page.
- Open [Lab Consequence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/lab-consequence/)
  when the question becomes whether a recommendation survives downstream assay
  cost, refusal, or outcome burden.
- Open [Maintenance](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintenance-overview/)
  when the question becomes which release gate or docs check should block the
  stronger wording.

## Best Reader Outcome

- a skeptical reviewer should leave knowing which owner currently deserves the
  final word
- a maintainer should leave knowing which sentence must narrow before release
- a scientist should leave knowing whether the real dispute is grounded
  evidence, analytical posture, or downstream burden

## Boundary

This route should explain who currently owns the decision question. It should
not replace the knowledge, intelligence, or lab owner surfaces themselves.
