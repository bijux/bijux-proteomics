# Architecture

`agentic-proteins` is the runtime authority for deterministic protein-design
execution.

Core design choices:

- execution paths are deterministic for equivalent inputs and policy controls
- run artifacts are first-class and inspectable
- runtime boundaries separate orchestration from domain governance owned by
  other packages

This package is the operational execution layer in the proteomics package map.
