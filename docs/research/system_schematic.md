# system_schematic  

**Scope:** One-page system schematic.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Components and boundaries are explicit.  
**Non-Goals:** Full architecture narrative.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc provides a single schematic.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Vocabulary aligns with [Core Concepts](../concepts/core_concepts.md).  

## Contracts  
Agents exchange signals within pathway edges.  
Constraints gate transitions and outputs.  
Regulator proposals remain bounded.  
Evidence uses [tests/unit/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_protein_system_rigidity.py).  

## Invariants  
Schematic elements stay aligned with [Core](../governance/core.md).  
Boundaries align with [Llm Authority](../architecture/llm_authority.md).  
Evidence aligns with [tests/unit/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_protein_system_rigidity.py).  

## Failure Modes  
Missing boundary labels weakens reviewability.  
Diagram drift breaks [Core](../governance/core.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Schematic updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when diagrams are generated.  
The replacement is [Architecture](../architecture/architecture.md).  
Obsolete docs are removed.  

Code refs: [tests/unit/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_protein_system_rigidity.py).  

```mermaid
flowchart LR
  AgentA -->|signal| AgentB
  AgentB -->|signal| AgentC
  Regulator -.->|proposal| AgentA
  Constraints --> AgentA
  Constraints --> AgentB
  Failure --> AgentC
```
