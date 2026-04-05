# reviewer_premortem  

**Scope:** Reviewer pre-mortem.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Anticipated critiques are explicit.  
**Non-Goals:** Debate.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc lists common review critiques.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Claim context lives in [Falsifiable Claim](falsifiable_claim.md).  

## Contracts  
Critique: “This is orchestration.” Response: signal scopes and pathway contracts show locality.  
Critique: “No intelligence.” Response: regulator proposals are bounded and measured.  
Critique: “Biology metaphor.” Response: constrained agents and pathways are explicit.  
Critique: “Over-engineered.” Response: invariants and failures are enforced.  
Evidence uses [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Invariants  
Critique list stays visible.  
Responses align with [Core](../governance/core.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Failure Modes  
Missing critiques weakens review readiness.  
Response drift breaks [Core](../governance/core.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when critiques are encoded.  
The replacement is [Metrics](../architecture/metrics.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  
