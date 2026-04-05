# Bijux Proteomics Core

`bijux-proteomics-core` defines the durable program entities for the umbrella repository:

- protein discovery programs
- explicit domain modules for targets, constraints, assays, reviews, and operating assumptions
- explicit biological domain modules for sequences, liabilities, and program lifecycle
- scientific constraints and review gates
- operating models for human review and lab feedback
- assay panels and success criteria
- schema-stamped documents that can be saved, loaded, and traced across systems
- repository and review protocols that keep storage and signoff adapters out of the domain layer
- execution adapters that can hand an approved sequence to `agentic_proteins`

This package is intentionally Python-first so the platform can be kicked off now without waiting on a Rust core.
