# anti_patterns  

**Scope:** Non-agentic anti-patterns.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Anti-patterns are explicit and rejected.  
**Non-Goals:** Exhaustive catalog.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc lists rejected patterns.  
Anti-patterns align with [Core](core.md).  
Architecture context lives in [Architecture](../architecture/architecture.md).  

## Contracts  
Direct state mutation bypasses [packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py).  
Hidden stochastic paths violate [Invariants](../architecture/invariants.md).  
Undeclared transitions violate [packages/agentic-proteins/src/agentic_proteins/biology/validation.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/validation.py).  

## Invariants  
Agent behavior stays within [Core Concepts](../concepts/core_concepts.md).  
Transition rules align with [Execution Model](../architecture/execution_model.md).  
Checks align with [packages/agentic-proteins/tests/unit/agents/test_protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/agents/test_protein_agent.py).  

## Failure Modes  
Bypass attempts break [Invariants](../architecture/invariants.md).  
Silent changes break [Core](core.md).  
Drift detection aligns with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Extension checks align with [packages/agentic-proteins/tests/unit/governance/test_module_stability.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/governance/test_module_stability.py).  
Extension docs align with [Docs Style](../meta/DOCS_STYLE.md).  

## Exit Criteria  
This doc is obsolete when anti-patterns are encoded.  
The replacement is [Invariants](../architecture/invariants.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py).  
