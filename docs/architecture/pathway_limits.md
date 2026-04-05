# pathway_limits  

**Scope:** Hard limits for agent interactions.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Limits are enforced at runtime.  
**Non-Goals:** Adaptive scaling.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines pathway interaction limits.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Docs Style](../meta/DOCS_STYLE.md) for structure.  

## Contracts  
Incoming signals per tick are capped.  
Outgoing signals per tick are capped.  
Dependency depth is capped.  

## Invariants  
Limits apply to every pathway.  
Limit violations stop execution.  
Limits are recorded in tests.  

## Failure Modes  
Limit violations raise errors.  
Silent overflow is rejected.  
Cycles are blocked by contract rules.  

## Extension Points  
Limit changes update [Execution Cost](execution_cost.md).  
Contract changes update [Architecture](architecture.md).  
Documentation updates follow [Triage](../meta/TRIAGE.md).  

## Exit Criteria  
This doc becomes obsolete when limits are generated.  
The replacement is [Architecture](architecture.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/biology/pathway.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/pathway.py).  
