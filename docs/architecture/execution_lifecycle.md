# execution_lifecycle  

**Scope:** Execution lifecycle state machine.  
**Audience:** Contributors and reviewers.  
**Guarantees:** States and transitions are explicit.  
**Non-Goals:** Alternate lifecycles.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the execution lifecycle state machine.  
Read [Architecture](architecture.md) for component context.  
Read [Core Concepts](../concepts/core_concepts.md) for vocabulary.  

## Contracts  
States and transitions are listed below.  
The lifecycle uses a single linear progression.  
Deviations are failures.  
- init -> plan  
- plan -> act  
- act -> observe  
- observe -> evaluate  
- evaluate -> terminate  
- terminate -> terminate  

## Invariants  
State order is init, plan, act, observe, evaluate, terminate.  
Each execution unit records its state.  
Transitions align with [Execution Model](execution_model.md).  

## Failure Modes  
Out-of-order transitions break traceability.  
Missing states break evaluation artifact records.  
Lifecycle drift breaks [Architecture](architecture.md).  

## Extension Points  
Lifecycle changes update [Execution Model](execution_model.md).  
Lifecycle changes update [Invariants](invariants.md).  
Lifecycle changes update [Core Concepts](../concepts/core_concepts.md).  

## Exit Criteria  
This doc becomes obsolete when execution is generated.  
The replacement is [Architecture](architecture.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/e2e/test_runtime_flow.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/e2e/test_runtime_flow.py).  
