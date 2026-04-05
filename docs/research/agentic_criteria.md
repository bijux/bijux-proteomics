# agentic_criteria  

**Scope:** Agentic criteria checklist.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Checklist entries map to evidence.  
**Non-Goals:** Marketing claims.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines a checklist for agentic criteria.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Vocabulary aligns with [Core Concepts](../concepts/core_concepts.md).  

## Contracts  
Checklist entries are fixed.  
Each entry maps to a test or artifact.  
Evidence is linked below.  
- Statefulness is verified in [packages/agentic-proteins/tests/unit/agents/test_protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/agents/test_protein_agent.py).  
- Autonomy bounds align with [Llm Authority](../architecture/llm_authority.md).  
- Decision locality aligns with [Execution Model](../architecture/execution_model.md).  
- Failure and recovery align with [Invariants](../architecture/invariants.md).  
- Non-orchestration aligns with [Execution Lifecycle](../architecture/execution_lifecycle.md).  

## Invariants  
Criteria remain consistent across releases.  
Criteria align with [Core](../governance/core.md).  
Criteria checks align with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Failure Modes  
Missing evidence breaks this checklist.  
Drift in criteria breaks [Core](../governance/core.md).  
Unlinked evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Criteria updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when criteria are encoded.  
The replacement is [Invariants](../architecture/invariants.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/unit/agents/test_protein_agent.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/agents/test_protein_agent.py).  
