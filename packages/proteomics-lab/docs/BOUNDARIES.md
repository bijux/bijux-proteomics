# Package boundaries

## Package identity

- Distribution name: `proteomics-lab`
- Import root: `proteomics_lab`
- Canonical behavior owner: `bijux-proteomics-lab`

## This package owns

- the short Lab installation and import names
- forwarding for supported assay planning, readiness, handoff, and outcome surfaces
- compatibility evidence for `proteomics_lab` callers

## This package does not own

- independent readiness, scheduling, custody, observation, or reconciliation policy
- upstream scientific computation, evidence truth, recommendation policy, or general orchestration
- authority to make an advisory plan executable without canonical readiness evidence

## Downstream expectations

The short import preserves canonical Lab artifact and refusal contracts.
Experimental policy and consequence interpretation boundaries remain defined by
`bijux-proteomics-lab`.

## Escalation signals

- route new assay and readiness behavior to canonical Lab first
- stop when alias code changes controls, authorization, custody, or outcome disposition
- escalate when a compatibility change could alter an executable handoff or historical observation

## Review questions

- do advisory, executable, refused, and observed outcomes match the canonical path
- is every alias export traceable to a supported Lab owner
- does the change preserve the separation between observation and interpretation
