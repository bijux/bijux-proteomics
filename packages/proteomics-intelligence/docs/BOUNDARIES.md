# Package boundaries

## Package identity

- Distribution name: `proteomics-intelligence`
- Import root: `proteomics_intelligence`
- Canonical behavior owner: `bijux-proteomics-intelligence`

## This package owns

- the short Intelligence installation and import names
- forwarding for supported ranking, challenge, recommendation, and refusal surfaces
- compatibility evidence for `proteomics_intelligence` callers

## This package does not own

- independent scoring, threshold, sensitivity, confidence, or recommendation policy
- scientific calculations, evidence custody, execution state, or lab authorization
- a decision posture different from canonical Intelligence

## Downstream expectations

Consumers using the short import must observe the canonical candidate and
decision contracts, including downgrade and refusal behavior. Policy changes
belong in `bijux-proteomics-intelligence`.

## Escalation signals

- route new decision policy and analytical judgment to canonical Intelligence
- stop when alias defaults or transformations can change a ranking or posture
- escalate when an API change affects persisted recommendations or supported callers

## Review questions

- are ranking, explanation, and refusal outputs identical through both paths
- is every alias export traceable to a canonical Intelligence owner
- does the change preserve the evidence and human-authority boundaries
