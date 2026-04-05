# TRIAGE  

**Scope:** Triage rules for documentation lifecycle.  
**Audience:** Contributors deciding doc changes.  
**Guarantees:** Docs exist only when tied to code.  
**Non-Goals:** Content authoring guidance.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one responsibility.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Docs Style](DOCS_STYLE.md) before edits.  
Read [Spine](SPINE.md) for context.  

## Contracts  
Each statement is a contract.  
Contracts align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
Contracts link to [Docs Style](DOCS_STYLE.md) and [Spine](SPINE.md).  

## Invariants  
Invariants describe stable behavior.  
Checks align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
Invariants align with [Docs Style](DOCS_STYLE.md).  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
Failures align with [Spine](SPINE.md).  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Docs Style](DOCS_STYLE.md).  
Extensions align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  

## Exit Criteria  
This doc becomes obsolete when the surface ends.  
The replacement is linked in [Spine](SPINE.md).  
Obsolete docs are removed.  

Code refs: [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
