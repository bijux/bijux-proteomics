---
title: Workflow Refusal Handbook
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-05-09
---

# Workflow Refusal Handbook

A refusal record distinguishes four operational responses. Each response preserves the current evidence and names what can happen next.

| response | meaning | next admissible action |
| --- | --- | --- |
| stop | the current handoff must not proceed | preserve state and inspect the named blocking condition |
| rerun | the question remains valid and recoverable evidence is missing or invalid | correct the declared condition and create a new run record |
| narrow | a weaker scope remains supported | issue a revised bounded question or recommendation |
| refuse | no responsible action exists inside the current policy or authority | retain the refusal until new evidence or authority changes the precondition |

### `dda`

- current posture: `recommend_with_downgrade`

#### stop when

- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not treat a single repeat as decision-grade if calibration drift reappears.
- Do not proceed if digest reproducibility control material is unavailable.

#### rerun when

- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- shared-peptide pressure changes protein-level conclusions even when peptide counts look stable
- contaminant promotion inflates confidence when blank carryover is not inspected

#### narrow when

- Cross-engine DDA drift still makes protein-facing promotion unsafe beyond the bounded benchmark story.
- Promote the paired DDA transfer loss into a dedicated literature-backed claim row and keep protein-facing trust downgraded until live replay or stronger cross-engine proof lands.
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation

#### refuse when

- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not treat a single repeat as decision-grade if calibration drift reappears.
- decision-grade condition is not satisfied: Target-decoy evidence remains visible and calibration stress does not collapse confidence framing.
- decision-grade condition is not satisfied: Comparator evidence or known-loss dossiers keep search-adapter behavior honest against external engines.

#### evidence paths

- `artifacts/intelligence/recommendation-packets/dda.json`
- `contradiction_triage:dda:1`
- `blank`
- `pooled_reference`
- `digest_reproducibility_reference`
- `carryover_blank`
- `artifacts/lab/flagship-follow-up-outcomes/dda.json`

### `dia`

- current posture: `recommend_with_downgrade`

#### stop when

- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not use the run for a decision-grade claim if the library reference is missing.
- Do not interpret successful extraction as biological closure when expected peptides still disappear without explanation.

#### rerun when

- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation
- vendor and library comparison gaps remain open
- comparator drift or missing external execution parity still materially limits this public workflow claim
- library incompleteness hides true peptide absence behind extraction failure
- ion-mobility or vendor-conditioned assumptions make the output look richer than the evidence posture warrants

#### narrow when

- DIA transition-grade confidence still conflicts with wider vendor- and library-parity expectations outsiders may assume.
- Keep DIA bounded to library-conditioned review until broader vendor-conditioned confrontation and rerun proof exist.
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation

#### refuse when

- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not use the run for a decision-grade claim if the library reference is missing.
- decision-grade condition is not satisfied: Import, transition, protein, and biological interpretation tiers all remain above bounded scientific thresholds.
- decision-grade condition is not satisfied: Library coverage, ion-mobility coverage, and absent-expected-peptide pressure all remain inside documented interpretation limits.
- library dependence was already the dominant public cap on DIA authority
- the thinner package family still showed unstable transfer under matrix shift
- The matrix-shift repeat exposed library-conditioned fragility, so the follow-up consumed queue and still forced the recommendation back to refusal.

#### evidence paths

- `artifacts/intelligence/recommendation-packets/dia.json`
- `contradiction_triage:dia:1`
- `blank`
- `pooled_reference`
- `library_reference`
- `bridge_sample`
- `artifacts/lab/flagship-follow-up-outcomes/dia.json`

### `lfq`

- current posture: `recommend_with_downgrade`

#### stop when

- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not spend the assay if only one extra sample can be added to a fragile contrast.
- Do not proceed when the run order and bridge design cannot be controlled tightly enough to learn anything new.

#### rerun when

- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- MNAR missingness makes the apparent rescue of a contrast look stronger than it is
- batch drift dominates the signal when bridge material is absent or underused

#### narrow when

- LFQ review-grade abundance confidence still conflicts with the harder cohort and missingness behavior named by the literature.
- Keep LFQ decision-grade wording blocked until harsher cohort pressure and observed outcome closure both exist.
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation

#### refuse when

- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not spend the assay if only one extra sample can be added to a fragile contrast.
- decision-grade condition is not satisfied: Missingness mechanism and replicate structure stay explicit enough that abundance summaries do not overclaim robustness.
- decision-grade condition is not satisfied: Batch posture and normalization drift remain inside bounded interpretation limits.
- repeatability was never the missing piece; cohort design weakness was
- the public package already showed missingness pressure large enough to block escalation
- The extra LFQ repeat only confirmed that missingness and cohort-shape weakness still dominate, so the loop consumed time without improving biological clarity.

#### evidence paths

- `artifacts/intelligence/recommendation-packets/lfq.json`
- `contradiction_triage:lfq:1`
- `blank`
- `pooled_reference`
- `batch_bridge`
- `replicate_balance_audit`
- `artifacts/lab/flagship-follow-up-outcomes/lfq.json`

### `multiplex`

- current posture: `do_not_recommend`

#### stop when

- no additional family-specific condition is published

#### rerun when

- public comparator-backed claim support is refused
- biological grounding remains thin
- vendor and library comparison gaps remain open
- operational burden remains too high for a justified recommendation

#### narrow when

- Multiplex has a paired public benchmark surface, but the companion stress result defeats outsider authority and no dedicated lab consequence packet closes the downstream gap.
- Keep multiplex internal support only until companion pressure passes and dedicated outsider review and lab consequence packets exist.

#### refuse when

- keep multiplex at internal support until the family earns its own outsider review and lab consequence closure
- Multiplex has a paired public benchmark surface, but the companion stress result defeats outsider authority and no dedicated lab consequence packet closes the downstream gap.

#### evidence paths

- `artifacts/intelligence/recommendation-packets/multiplex.json`
- `contradiction_triage:multiplex:1`

### `ptm`

- current posture: `recommend_with_downgrade`

#### stop when

- operational burden remains too high for a justified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not proceed when site ambiguity is still the main story.

#### rerun when

- operational burden remains too high for a justified recommendation
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- site ambiguity survives the rerun and leaves the lab with a more expensive version of the same story
- enrichment or motif pressure creates a convincing signal without a targetable site-specific conclusion

#### narrow when

- PTM localization confidence still conflicts with the temptation to read occupancy or regulation into a narrower phospho-oriented evidence surface.
- Keep PTM release language bounded to localization and ambiguity until broader family-specific comparator pressure exists.
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation

#### refuse when

- operational burden remains too high for a justified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- decision-grade condition is not satisfied: Localization confidence remains high enough that ambiguous site groups do not dominate the claimed biology.
- decision-grade condition is not satisfied: Only PTM families with explicit credibility tracks and scope limits can support decision-facing interpretation.

#### evidence paths

- `artifacts/intelligence/recommendation-packets/ptm.json`
- `contradiction_triage:ptm:1`
- `enrichment_blank`
- `site_localization_reference`
- `unmodified_counterpart_control`
- `artifacts/lab/flagship-follow-up-outcomes/ptm.json`

### `targeted`

- current posture: `recommend_with_downgrade`

#### stop when

- operational burden remains too high for a justified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- Do not proceed when heavy references or calibration standards are missing.

#### rerun when

- operational burden remains too high for a justified recommendation
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- coeluting interference produces clean-looking transitions that still misstate the biology
- heavy-light mismatch or calibration drift turns the panel into an operationally neat but scientifically weak artifact

#### narrow when

- Targeted operator-facing confidence still conflicts with missing Skyline-class comparator and calibration realism.
- Keep targeted language out of calibration-clean and vendor-parity authority until the missing confrontation lands.
- external comparator claim support is still advisory
- claim support is not yet strong enough for an unqualified recommendation

#### refuse when

- operational burden remains too high for a justified recommendation
- comparator drift or missing external execution parity still materially limits this public workflow claim
- decision-grade condition is not satisfied: Chromatogram QC, calibration standards, and interference behavior all remain explicit before transition handoff.
- decision-grade condition is not satisfied: Blank, heavy-reference, and calibration-standard controls all stay visible before claims leave advisory status.

#### evidence paths

- `artifacts/intelligence/recommendation-packets/targeted.json`
- `contradiction_triage:targeted:1`
- `blank`
- `heavy_reference`
- `calibration_standard`
- `interference_scout_injection`
- `artifacts/lab/flagship-follow-up-outcomes/targeted.json`

## Rule

If the best downstream action is stop, rerun, narrow, or refuse, the public recommendation remains weaker than a full recommendation. A retry creates a new run or decision record; it does not erase the refusal that justified it.
