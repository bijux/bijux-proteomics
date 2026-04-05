# surface_area  

**Scope:** Surface-area budgeting.  
**Audience:** External users and contributors.  
**Guarantees:** Public surface stays bounded.  
**Non-Goals:** Full API listing.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines surface-area budgets.  
MPI context lives in [Mpi](mpi.md).  
Architecture context lives in [Invariants](../architecture/invariants.md).  

## Contracts  
Public entry points are capped by [packages/agentic-proteins/src/agentic_proteins/core/surface_area.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/surface_area.py).  
Extension points are capped by the same budget.  
Configuration knobs are capped by the same budget.  

## Invariants  
Budgets align with [Core](../governance/core.md).  
Budget checks align with [packages/agentic-proteins/tests/unit/governance/test_surface_area_budget.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/governance/test_surface_area_budget.py).  
Budget changes update [Mpi](mpi.md).  

## Failure Modes  
Budget overruns trigger review.  
Untracked entry points break [Core](../governance/core.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Mpi](mpi.md).  

## Exit Criteria  
This doc is obsolete when budgets are generated.  
The replacement is [Mpi](mpi.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/core/surface_area.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/surface_area.py).  
