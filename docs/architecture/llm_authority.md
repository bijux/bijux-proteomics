# llm_authority  

**Scope:** LLM authority boundary.  
**Audience:** Contributors and reviewers.  
**Guarantees:** LLM actions are bounded and enforced.  
**Non-Goals:** Model benchmarking.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the LLM authority boundary.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Core Concepts](../concepts/core_concepts.md) for vocabulary.  
Read [Docs Style](../meta/DOCS_STYLE.md) for structure.  

## Contracts  
Allowed actions are tuning only.  
Forbidden actions include any state mutation.  
Read-only and write-through permissions are explicit.  

## Invariants  
Proposals never mutate state directly.  
Validation rejects invalid proposals.  
Approvals gate all proposal application.  

## Failure Modes  
Forbidden actions raise errors.  
Invalid proposals are rejected and logged.  
Missing approvals block proposal application.  

## Extension Points  
Authority changes update [Docs Style](../meta/DOCS_STYLE.md).  
Authority changes update [Core Concepts](../concepts/core_concepts.md).  
Authority changes update [Architecture](architecture.md).  

## Exit Criteria  
This doc becomes obsolete when authority is generated.  
The replacement is [Architecture](architecture.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/biology/regulator.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/regulator.py).  
