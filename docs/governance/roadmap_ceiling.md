# roadmap_ceiling  

**Scope:** Research roadmap ceiling.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Out-of-scope areas are explicit.  
**Non-Goals:** Feature backlog.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc states explicit research ceilings.  
Ceilings align with [Core](core.md).  
Architecture context lives in [Architecture](../architecture/architecture.md).  

## Contracts  
The system avoids unsupervised topology mutation.  
The system avoids hidden state mutation in [packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py).  
The system avoids replacing contract locks in [packages/agentic-proteins/src/agentic_proteins/core/api_lock.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/api_lock.py).  

## Invariants  
Ceilings align with [Invariants](../architecture/invariants.md).  
Ceilings align with [Experimental](../architecture/experimental.md).  
Checks align with [packages/agentic-proteins/tests/unit/core/test_core_api_lock.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/core/test_core_api_lock.py).  

## Failure Modes  
Scope drift breaks [Core](core.md).  
Implicit expansion breaks [Invariants](../architecture/invariants.md).  
Untracked changes break [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Extension docs align with [Docs Style](../meta/DOCS_STYLE.md).  
Extension checks align with [packages/agentic-proteins/tests/unit/governance/test_module_stability.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/governance/test_module_stability.py).  

## Exit Criteria  
This doc is obsolete when scope is encoded.  
The replacement is [Core](core.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/core/api_lock.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/api_lock.py).  
