# misuse_guards  

**Scope:** Runtime misuse guards.  
**Audience:** External users and contributors.  
**Guarantees:** Guardrails fail loudly.  
**Non-Goals:** Error recovery policy.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc lists misuse guards.  
MPI context lives in [Mpi](mpi.md).  
Architecture context lives in [Invariants](../architecture/invariants.md).  

## Contracts  
Direct state mutation is rejected by [ProteinAgent](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py).  
Invariant checks run per tick in [PathwayExecutor](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/pathway.py).  
Unauthorized LLM actions raise in [LLMRegulator](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/regulator.py).  

## Invariants  
Guards align with [Core](../governance/core.md).  
Guard tests align with [tests/unit/test_protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_protein_agent.py).  
Guard tests align with [tests/unit/test_llm_regulator.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_llm_regulator.py).  

## Failure Modes  
Bypass attempts break [Invariants](../architecture/invariants.md).  
Silent failures break [Core](../governance/core.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Surface Area](surface_area.md).  

## Exit Criteria  
This doc is obsolete when guards are generated.  
The replacement is [Invariants](../architecture/invariants.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py).  
