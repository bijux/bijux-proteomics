# Package boundaries

## Package identity

- Distribution name: `proteomics-runtime`
- Import root: `proteomics_runtime`
- Canonical behavior owner: `bijux-proteomics-runtime`

## This package owns

- the short Runtime installation, import, and command names
- forwarding to canonical application, provider, run, and workflow surfaces
- compatibility evidence for callers using `proteomics_runtime`

## This package does not own

- independent execution planning, provider selection, state, artifacts, or recovery policy
- scientific workflow semantics, evidence truth, recommendation policy, or lab readiness
- package-local operational claims unsupported by alias tests

## Downstream expectations

The alias provides naming compatibility, not a second execution product.
Operational evidence and new Runtime behavior remain in
`bijux-proteomics-runtime`.

## Escalation signals

- route new execution and provider behavior to canonical Runtime first
- stop when alias code begins producing independent state or artifact semantics
- escalate when command, configuration, API, or persisted-state behavior diverges

## Review questions

- is the change forwarding-only and covered by observable compatibility tests
- would canonical Runtime callers receive the same outcome and failure behavior
- are operational claims supported by canonical evidence rather than alias prose
