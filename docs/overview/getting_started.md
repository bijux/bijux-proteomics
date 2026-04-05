# getting_started  

**Scope:** Single install and run path.  
**Audience:** Users running the CLI.  
**Guarantees:** One reproducible path with fixed assumptions.  
**Non-Goals:** Alternative setups or options.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
Getting started defines one install and run path.  
Read [Core Concepts](../concepts/core_concepts.md) for vocabulary.  
Read [Dependencies](../security/dependencies.md) for dependency constraints. <!-- docs/security/ -->  
Architecture components are defined in [Architecture](../architecture/architecture.md).  

## Contracts  
Install with `pipx install agentic-proteins`.  
Run with `agentic-proteins run --sequence "ACDEFGHIKLMNPQRSTVWY"`.  
Artifacts are stored under `artifacts/<run_id>/`.  

## Invariants  
Local filesystem permissions prevent cross-tenant access.  
Providers return deterministic results for fixed inputs.  
CI artifacts are not tampered with between steps.  

## Failure Modes  
Missing allowlist dependencies in [Dependencies](../security/dependencies.md) break this path. <!-- docs/security/ -->  
Assumptions are tracked in [Threat Model](../security/threat_model.md). <!-- docs/security/ -->  
Invalid sequences fail validation.  

## Extension Points  
Changes update [Cli](../cli/cli.md).  
Dependency changes update [Dependencies](../security/dependencies.md). <!-- docs/security/ -->  
Vocabulary changes update [Core Concepts](../concepts/core_concepts.md).  

## Exit Criteria  
This doc becomes obsolete when a generated entrypoint replaces it.  
The replacement is [Index](../index.md).  
Obsolete docs are removed.  

Code refs: [tests/integration/test_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/integration/test_cli.py).  
