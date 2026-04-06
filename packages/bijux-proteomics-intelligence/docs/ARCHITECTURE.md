# Architecture

`bijux-proteomics-intelligence` transforms program and evidence context into
explainable candidate decisions.

Core design choices:

- ranking policy is explicit and serializable
- every rejection is accompanied by structured reason codes
- scenario recommendations are deterministic for a fixed policy and inputs

The package emphasizes auditability over opaque scoring.
