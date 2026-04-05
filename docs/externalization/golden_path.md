# golden_path  

**Scope:** Canonical golden path example.  
**Audience:** External users and contributors.  
**Guarantees:** Example uses MPI only.  
**Non-Goals:** Full tutorial.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc points to the canonical example.  
MPI context lives in [Mpi](mpi.md).  
Architecture context lives in [Architecture](../architecture/architecture.md).  

## Contracts  
The example uses only MPI entry points.  
The example shows agenticity, failure, and recovery.  
The example runtime stays under 60 seconds on default hardware.  
Example code lives in [scripts/golden_path_example.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/golden_path_example.py).  

## Invariants  
The golden path remains single and canonical.  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  
MPI meaning aligns with [Core Concepts](../concepts/core_concepts.md).  

## Failure Modes  
Multiple examples dilute [Mpi](mpi.md).  
Hidden dependencies break [Core](../governance/core.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Surface Area](surface_area.md).  

## Exit Criteria  
This doc is obsolete when examples are generated.  
The replacement is [Mpi](mpi.md).  
Obsolete docs are removed.  

Code refs: [scripts/golden_path_example.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/golden_path_example.py).  
