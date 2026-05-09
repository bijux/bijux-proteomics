---
title: Outcome Learning Loops
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-05-09
---

# Outcome Learning Loops

These loops record how requested-versus-observed follow-up should tighten or weaken the next recommendation. They keep assay burden, blocked assays, weakened evidence, and changed posture visible together instead of treating the next recommendation as memoryless.

### `dda`

- initial posture: `recommend_with_downgrade`
- revised posture after outcome: `recommend_with_downgrade`
- worth the assay spend: yes
- requested assays: `dda-repeat-digest`, `dda-pooled-reference`, `dda-carryover-blank`
- observed assays: `dda-repeat-digest`, `dda-pooled-reference`, `dda-carryover-blank`
- matched assays: `dda-repeat-digest`, `dda-pooled-reference`, `dda-carryover-blank`
- blocked assays: none
- weakened assays: none
- learning points: matched assays preserved the intended closure loop without widening public language, the follow-up repaid cost because it stabilized the contaminant and pooled-reference boundary
- next adjustments: matched assays preserved the intended closure loop without widening public language, the follow-up repaid cost because it stabilized the contaminant and pooled-reference boundary
- evidence paths: `artifacts/lab/flagship-follow-up-outcomes/dda.json`, `claim:dda_target_decoy_stability`

### `dia`

- initial posture: `recommend_with_downgrade`
- revised posture after outcome: `do_not_recommend`
- worth the assay spend: no
- requested assays: `dia-library-bridge`, `dia-matrix-shift-repeat`
- observed assays: `dia-matrix-shift-repeat`
- matched assays: `dia-matrix-shift-repeat`
- blocked assays: `dia-library-bridge`
- weakened assays: `dia-matrix-shift-repeat`
- learning points: requested assay loss should block any attempt to treat DIA follow-up as laboratory closure, strong import-backed review does not rescue a loop that fails its own library bridge
- next adjustments: requested assay loss should block any attempt to treat DIA follow-up as laboratory closure, strong import-backed review does not rescue a loop that fails its own library bridge, feed the revised follow-up result back into future recommendation posture instead of keeping the original recommendation sentence unchanged, treat blocked assays as explicit evidence for narrower or slower future follow-up, carry weakened assays forward as downgrade evidence rather than as partial confirmation
- evidence paths: `artifacts/lab/flagship-follow-up-outcomes/dia.json`

### `lfq`

- initial posture: `do_not_recommend`
- revised posture after outcome: `do_not_recommend`
- worth the assay spend: no
- requested assays: `lfq-extra-replicate-block`, `lfq-randomized-repeat`
- observed assays: `lfq-extra-replicate-block`
- matched assays: `lfq-extra-replicate-block`
- blocked assays: `lfq-randomized-repeat`
- weakened assays: `lfq-extra-replicate-block`
- learning points: low-information repeats should stay refused when the biological conclusion is still design-limited
- next adjustments: low-information repeats should stay refused when the biological conclusion is still design-limited, treat blocked assays as explicit evidence for narrower or slower future follow-up, carry weakened assays forward as downgrade evidence rather than as partial confirmation
- evidence paths: `artifacts/lab/flagship-follow-up-outcomes/lfq.json`

### `multiplex`

- initial posture: `do_not_recommend`
- revised posture after outcome: `do_not_recommend`
- worth the assay spend: no
- requested assays: 
- observed assays: 
- matched assays: none
- blocked assays: none
- weakened assays: none
- learning points: no shipped requested-versus-observed outcome loop exists for this family yet
- next adjustments: publish a dedicated downstream lab consequence and observed outcome loop before strengthening recommendation posture
- evidence paths: `artifacts/intelligence/recommendation-packets/multiplex.json`

### `ptm`

- initial posture: `do_not_recommend`
- revised posture after outcome: `recommend_with_downgrade`
- worth the assay spend: yes
- requested assays: `ptm-site-targetability`, `ptm-orthogonal-validation`
- observed assays: `ptm-site-targetability`, `ptm-orthogonal-validation`
- matched assays: `ptm-site-targetability`, `ptm-orthogonal-validation`
- blocked assays: none
- weakened assays: `ptm-site-targetability`
- learning points: site-level ambiguity can still repay follow-up when the closure question is narrow and explicitly targetable, useful PTM follow-up should strengthen a bounded claim rather than erase the wider ambiguity warning
- next adjustments: site-level ambiguity can still repay follow-up when the closure question is narrow and explicitly targetable, useful PTM follow-up should strengthen a bounded claim rather than erase the wider ambiguity warning, feed the revised follow-up result back into future recommendation posture instead of keeping the original recommendation sentence unchanged, carry weakened assays forward as downgrade evidence rather than as partial confirmation
- evidence paths: `artifacts/lab/flagship-follow-up-outcomes/ptm.json`, `claim:ptm_site_resolution_boundary`

### `targeted`

- initial posture: `do_not_recommend`
- revised posture after outcome: `recommend_with_downgrade`
- worth the assay spend: yes
- requested assays: `prm-assay`, `orthogonal-assay`
- observed assays: `prm-assay`, `orthogonal-assay`
- matched assays: `prm-assay`, `orthogonal-assay`
- blocked assays: none
- weakened assays: none
- learning points: fast calibration-facing loops can be worth it even when broader targeted authority remains bounded, follow-up value here comes from interference clarification, not from pretending vendor-parity authority exists
- next adjustments: fast calibration-facing loops can be worth it even when broader targeted authority remains bounded, follow-up value here comes from interference clarification, not from pretending vendor-parity authority exists, feed the revised follow-up result back into future recommendation posture instead of keeping the original recommendation sentence unchanged
- evidence paths: `artifacts/lab/flagship-follow-up-outcomes/targeted.json`, `claim:targeted_transition_consistency`, `claim:targeted_interference_boundary`

## Boundary

A recommendation that changes after one shipped follow-up loop should not keep its old public sentence by inertia.
