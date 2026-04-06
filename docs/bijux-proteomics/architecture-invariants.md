# Architecture Invariants

The repository keeps the following architecture invariants:

- package boundaries remain explicit and import directions stay acyclic
- domain runtime code and maintenance tooling stay in separate packages
- every quality gate has deterministic behavior for identical repository state
