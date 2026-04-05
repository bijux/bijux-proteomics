# positioning  

**Scope:** Final positioning choice.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Position is explicit.  
**Non-Goals:** Market analysis.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the final positioning.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Vocabulary aligns with [Core Concepts](../concepts/core_concepts.md).  

## Contracts  
Positioning is agent systems research.  
Computational biology context is modeled, not claimed as primary.  
Hybrid simulation framing is limited to pathway execution.  
Evidence uses [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Invariants  
Positioning stays fixed across releases.  
Positioning aligns with [Core](core.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Failure Modes  
Ambiguous positioning weakens reviewability.  
Position drift breaks [Core](core.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Position updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when positioning is encoded.  
The replacement is [Core](core.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  
