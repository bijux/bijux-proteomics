# SPINE  

**Scope:** Single navigation spine for docs/.  
**Audience:** Readers consuming docs top-down.  
**Guarantees:** Lists all docs in order.  
**Non-Goals:** Per-topic READMEs.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one responsibility.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Index](../index.md) before edits.  
Read [Docs Style](DOCS_STYLE.md) for context.  

## Contracts  
Each statement is a contract.  
Contracts align with [mkdocs.yml](https://github.com/bijux/bijux-proteomics/blob/main/mkdocs.yml).  
Contracts link to [Index](../index.md) and [Docs Style](DOCS_STYLE.md).  

## Invariants  
Invariants describe stable behavior.  
Checks align with [mkdocs.yml](https://github.com/bijux/bijux-proteomics/blob/main/mkdocs.yml).  
Invariants align with [Index](../index.md).  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [mkdocs.yml](https://github.com/bijux/bijux-proteomics/blob/main/mkdocs.yml).  
Failures align with [Docs Style](DOCS_STYLE.md).  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Index](../index.md).  
Extensions align with [mkdocs.yml](https://github.com/bijux/bijux-proteomics/blob/main/mkdocs.yml).  

## Exit Criteria  
This doc becomes obsolete when the surface ends.  
The replacement is linked in [Docs Style](DOCS_STYLE.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  
Docs list:  
- [Docs Style](DOCS_STYLE.md)  
- [Docs Voice](DOCS_VOICE.md)  
- [Naming](NAMING.md)  
- [Triage](TRIAGE.md)  
- [Spine](SPINE.md)  
- [Index](../index.md)  
- [Getting Started](../overview/getting_started.md)  
- [Core Concepts](../concepts/core_concepts.md)  
- [Core](../governance/core.md)  
- [Semver](../governance/semver.md)  
- [Anti Patterns](../governance/anti_patterns.md)  
- [Roadmap Ceiling](../governance/roadmap_ceiling.md)  
- [Positioning](../governance/positioning.md)  
- [Release Identity](../governance/release_identity.md)  
- [Agentic Criteria](../research/agentic_criteria.md)  
- [Agent Taxonomy](../research/agent_taxonomy.md)  
- [Formal Model](../research/formal_model.md)  
- [Falsifiable Claim](../research/falsifiable_claim.md)  
- [Decisive Experiment](../research/decisive_experiment.md)  
- [Ablation Studies](../research/ablation_studies.md)  
- [Neutral Results](../research/neutral_results.md)  
- [Reviewer Premortem](../research/reviewer_premortem.md)  
- [System Schematic](../research/system_schematic.md)  
- [Mpi](../externalization/mpi.md)  
- [Golden Path](../externalization/golden_path.md)  
- [Misuse Guards](../externalization/misuse_guards.md)  
- [Surface Area](../externalization/surface_area.md)  
- [Sandbox](../externalization/sandbox.md)  
- [Invariant Visualization](../externalization/invariant_visualization.md)  
- [Why Not X](../externalization/why_not_x.md)  
- [Architecture](../architecture/architecture.md)  
- [Invariants](../architecture/invariants.md)  
- [Experimental](../architecture/experimental.md)  
- [Llm Authority](../architecture/llm_authority.md)  
- [Execution Model](../architecture/execution_model.md)  
- [Execution Lifecycle](../architecture/execution_lifecycle.md)  
- [Design Debt](../architecture/design_debt.md)  
- [Cli](../cli/cli.md)  
- [Cli Surface](../interface/cli_surface.md)  
- [Overview](../api/overview.md)  
- [Schema](../api/schema.md)  
- [Dependencies](../security/dependencies.md)  
- [Threat Model](../security/threat_model.md)  
