# invariant_visualization  

**Scope:** Invariant visualization tooling.  
**Audience:** External users and contributors.  
**Guarantees:** Per-tick invariants are observable.  
**Non-Goals:** GUI tooling.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc describes invariant visualization.  
Architecture context lives in [Conservation](../architecture/conservation.md).  
Metrics context lives in [Metrics](../architecture/metrics.md).  

## Contracts  
Per-tick invariant snapshots are recorded by [PathwayExecutor](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/pathway.py).  
Violations are captured in the invariant log.  
Visualization uses [scripts/visualize_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/visualize_invariants.py).  

## Invariants  
Invariant visibility aligns with [Invariants](../architecture/invariants.md).  
Snapshot format aligns with [tests/unit/test_execution_cost.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_execution_cost.py).  
MPI meaning aligns with [Mpi](mpi.md).  

## Failure Modes  
Missing snapshots hide violations.  
Drift in logs breaks [Conservation](../architecture/conservation.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Surface Area](surface_area.md).  

## Exit Criteria  
This doc is obsolete when visualization is generated.  
The replacement is [Metrics](../architecture/metrics.md).  
Obsolete docs are removed.  

Code refs: [scripts/visualize_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/visualize_invariants.py).  
