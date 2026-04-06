# Architecture

`bijux-proteomics-core` models the program-centric domain: targets, constraints,
assays, review gates, lifecycle transitions, and execution adapter protocols.

Core design choices:

- domain entities are explicit and strongly typed
- review and lifecycle rules are model-level invariants
- execution integration stays behind protocol boundaries

The package is designed as the durable semantic source of truth for progression
and review behavior.
