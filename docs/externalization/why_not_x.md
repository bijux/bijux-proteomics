# why_not_x  

**Scope:** Why-not-X contrasts.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Contrasts are explicit.  
**Non-Goals:** Full survey.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc lists explicit contrasts.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
MPI context lives in [Mpi](mpi.md).  

## Contracts  
Workflow engines focus on orchestration, while this system focuses on bounded state transitions.  
Classic MAS frameworks optimize global coordination, while this system enforces local contracts.  
End-to-end LLM agents blur control, while this system enforces regulator boundaries.  

## Invariants  
Contrasts align with [Core](../governance/core.md).  
Contrasts align with [Execution Model](../architecture/execution_model.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Failure Modes  
Missing contrasts weakens reviewability.  
Contrast drift breaks [Core](../governance/core.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Surface Area](surface_area.md).  

## Exit Criteria  
This doc is obsolete when contrasts are encoded.  
The replacement is [Core](../governance/core.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  
