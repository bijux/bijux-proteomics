# agent_taxonomy  

**Scope:** Mapping to agent taxonomies.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Contrasts are explicit.  
**Non-Goals:** Exhaustive survey.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc maps the system to known taxonomies.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Vocabulary aligns with [Core Concepts](../concepts/core_concepts.md).  

## Contracts  
BDI agents use belief, desire, intention loops.  
This system uses fixed transition rules instead of deliberation.  
Reactive agents use direct stimulus-response rules.  
This system adds constraints and failure states beyond direct reactions.  
MDP agents assume global policy optimization.  
This system uses local transition validation without global policy search.  
Multi-agent systems focus on interaction graphs.  
This system uses explicit signal scopes and pathway contracts.  

## Invariants  
Taxonomy mapping stays consistent.  
Mapping aligns with [Invariants](../architecture/invariants.md).  
Evidence aligns with [tests/unit/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_protein_system_rigidity.py).  

## Failure Modes  
Unstated contrasts weaken reviewability.  
Drift in mapping breaks [Core](../governance/core.md).  
Unlinked references break [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Mapping updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when mapping is encoded.  
The replacement is [Architecture](../architecture/architecture.md).  
Obsolete docs are removed.  

Code refs: [tests/unit/test_protein_system_rigidity.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_protein_system_rigidity.py).  
