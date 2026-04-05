# sandbox  

**Scope:** Sandbox separation.  
**Audience:** External users and contributors.  
**Guarantees:** Core and sandbox remain distinct.  
**Non-Goals:** Sandbox feature catalog.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the sandbox split.  
Core context lives in [Core](../governance/core.md).  
Experimental context lives in [Experimental](../architecture/experimental.md).  

## Contracts  
Core modules live under [packages/agentic-proteins/src/agentic_proteins/core](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core).  
Sandbox modules live under [packages/agentic-proteins/src/agentic_proteins/sandbox](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/sandbox/__init__.py).  
Sandbox code is marked experimental.  

## Invariants  
Core stability aligns with [Invariants](../architecture/invariants.md).  
Sandbox usage aligns with [Experimental](../architecture/experimental.md).  
Evidence aligns with [packages/agentic-proteins/tests/unit/governance/test_module_stability.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/governance/test_module_stability.py).  

## Failure Modes  
Mixing core and sandbox breaks [Core](../governance/core.md).  
Unlabeled sandbox code breaks [Experimental](../architecture/experimental.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Mpi](mpi.md).  

## Exit Criteria  
This doc is obsolete when sandbox is removed.  
The replacement is [Experimental](../architecture/experimental.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/sandbox/__init__.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/sandbox/__init__.py).  
