# formal_model  

**Scope:** Minimal formal model.  
**Audience:** Reviewers and contributors.  
**Guarantees:** State and constraint sets are explicit.  
**Non-Goals:** Full proofs.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines a minimal formal model.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Vocabulary aligns with [Core Concepts](../concepts/core_concepts.md).  

## Contracts  
State space S is the set of agent states.  
Action space A is the set of signals.  
Transition function T maps (S, A) to S.  
Constraint set C limits valid transitions.  
Constraints align with [Invariants](../architecture/invariants.md).  
Validation uses [packages/agentic-proteins/tests/unit/agents/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/agents/test_protein_system_rigidity.py).  

## Invariants  
S, A, T, and C remain consistent.  
Definitions align with [Core](../governance/core.md).  
Evidence aligns with [packages/agentic-proteins/tests/unit/agents/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/agents/test_protein_system_rigidity.py).  

## Failure Modes  
Ambiguous symbols break reviewability.  
Drift in definitions breaks [Core](../governance/core.md).  
Unlinked references break [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Model updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when a formal spec exists.  
The replacement is [Architecture](../architecture/architecture.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/unit/agents/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/agents/test_protein_system_rigidity.py).  
