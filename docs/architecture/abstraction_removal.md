# abstraction_removal  

**Scope:** Removal of unused abstraction layers.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Removed layers are documented and tested.  
**Non-Goals:** Historical narrative.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc records the abstraction removal.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Docs Style](../meta/DOCS_STYLE.md) for structure.  

## Contracts  
The contracts interface layer was removed.  
The registry base class was removed.  
The registry re-export indirection was removed.  

## Invariants  
Direct imports replace removed layers.  
Registry behavior remains explicit.  
Public interfaces remain tested.  

## Failure Modes  
Missing imports fail tests.  
Unexpected coupling fails review.  
Undefined layers are rejected.  

## Extension Points  
Removals update [Design Debt](design_debt.md).  
Public interface changes update [Core](../governance/core.md).  
Documentation updates follow [Triage](../meta/TRIAGE.md).  

## Exit Criteria  
This doc becomes obsolete when removals are generated.  
The replacement is [Core](../governance/core.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/registry/agents.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/registry/agents.py).  
