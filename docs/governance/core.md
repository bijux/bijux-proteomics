# core  

**Scope:** Non-negotiable core definition.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Core meaning does not drift.  
**Non-Goals:** Feature rationale.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the immutable core.  
Core terms align with [Core Concepts](../concepts/core_concepts.md).  
Architecture context lives in [Architecture](../architecture/architecture.md).  

## Contracts  
Core meaning binds agent, pathway, and cell roles.  
Contract locks live in [Invariants](../architecture/invariants.md).  
Evidence uses [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Invariants  
Core meaning stays fixed across releases.  
Core meaning aligns with [Invariants](../architecture/invariants.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Failure Modes  
Core drift breaks [Invariants](../architecture/invariants.md).  
Untracked changes break [Core Concepts](../concepts/core_concepts.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Extension rules align with [Docs Style](../meta/DOCS_STYLE.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when the core is encoded.  
The replacement is [Architecture](../architecture/architecture.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  
