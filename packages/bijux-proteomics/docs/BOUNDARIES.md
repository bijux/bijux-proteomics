# Package boundaries

## Package identity

- Distribution name: `bijux-proteomics`
- Import root: `bijux_proteomics`
- Canonical behavior owner: `bijux-proteomics-core`

## This package owns

- the `bijux-proteomics` distribution name and installation contract
- the canonical `bijux-proteomics` command exposure
- packaging metadata that installs the Core-owned `bijux_proteomics` namespace

## This package does not own

- scientific models, algorithms, workflow contracts, or benchmark acceptance
- Runtime execution, evidence reconciliation, recommendation policy, or lab planning
- a second implementation beneath the alias metadata helper

## Downstream expectations

Consumers may install this distribution as the primary scientific entrypoint,
but behavior and API meaning remain owned by `bijux-proteomics-core`. Package
metadata and command routing must remain consistent with that canonical owner.

## Escalation signals

- route scientific behavior changes to `bijux-proteomics-core` before changing this distribution
- stop when alias-local code begins implementing a scientific or workflow decision
- escalate release review when metadata, command routing, or installed namespace content diverges from Core

## Review questions

- does the change preserve one canonical implementation of `bijux_proteomics`
- do installation and command behavior still match the Core distribution contract
- can the alias metadata helper remain private and behavior-free
