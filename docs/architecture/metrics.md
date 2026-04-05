# metrics  

**Scope:** Minimal metrics set.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Metrics are defined and computed.  
**Non-Goals:** Comprehensive analytics.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the minimal metrics set.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Execution Cost](execution_cost.md) for cost context.  

## Contracts  
Pathway throughput is reported.  
Failure rate is reported.  
Recovery success is reported.  
Signal entropy is reported.  
LLM intervention delta is reported.  

## Invariants  
Metrics are computed from event logs.  
Metrics never mutate pathway state.  
Metrics are deterministic for fixed logs.  

## Failure Modes  
Missing metrics fail tests.  
Undefined metrics are rejected.  
Non-deterministic metrics are rejected.  

## Extension Points  
Metric changes update [Execution Cost](execution_cost.md).  
Stress tests update [Pathway Limits](pathway_limits.md).  
Documentation updates follow [Triage](../meta/TRIAGE.md).  

## Exit Criteria  
This doc becomes obsolete when metrics are generated.  
The replacement is [Execution Cost](execution_cost.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/biology/pathway.py](https://github.com/bijux/agentic-proteins/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/pathway.py).  
