# execution_model  

**Scope:** Deterministic versus agentic boundary.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Boundaries are explicit and testable.  
**Non-Goals:** Provider-specific behavior.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines deterministic and agentic boundaries.  
Read [Architecture](architecture.md) for component context.  
Read [Core Concepts](../concepts/core_concepts.md) for vocabulary.  

## Contracts  
Deterministic behavior covers state transitions and artifact hashing.  
The execution contract is recorded in [packages/agentic-proteins/src/agentic_proteins/core/contracts.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/contracts.py).  
Agentic behavior is limited to provider outputs and selection.  

## Invariants  
Deterministic paths use fixed inputs and seeds.  
Agentic paths record every decision and output.  
Boundaries align with [Invariants](invariants.md).  

## Failure Modes  
Untracked stochastic output breaks reproducibility.  
Missing logs break traceability.  
Boundary drift breaks [Architecture](architecture.md).  

## Extension Points  
Boundary changes update [Execution Lifecycle](execution_lifecycle.md).  
Boundary changes update [Invariants](invariants.md).  
Boundary changes update [Core Concepts](../concepts/core_concepts.md).  

## Exit Criteria  
This doc becomes obsolete when execution is generated.  
The replacement is [Architecture](architecture.md).  
Obsolete docs are removed.  

Code refs: [tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/regression/test_architecture_invariants.py).  
