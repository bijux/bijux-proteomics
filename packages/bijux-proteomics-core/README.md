# Bijux Proteomics Core

`bijux-proteomics-core` defines the durable program entities for the umbrella repository:

- protein discovery programs
- scientific constraints and review gates
- operating models for human review and lab feedback
- assay panels and success criteria
- execution adapters that can hand an approved sequence to `agentic_proteins`

This package is intentionally Python-first so the platform can be kicked off now without waiting on a Rust core.
