# falsifiable_claim  

**Scope:** Single falsifiable claim.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Claim is testable.  
**Non-Goals:** Multiple hypotheses.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc states one falsifiable claim.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Vocabulary aligns with [Core Concepts](../concepts/core_concepts.md).  

## Contracts  
Claim: bounded regulator proposals improve recovery rate without raising failure rate.  
Recovery rate is computed in [Metrics](../architecture/metrics.md).  
Failure rate is computed in [Metrics](../architecture/metrics.md).  
Evidence uses [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  

## Invariants  
Claim wording stays fixed.  
Claim aligns with [Core](../governance/core.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  

## Failure Modes  
Unclear claim blocks experiments.  
Claim drift breaks [Core](../governance/core.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Claim updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when claim is replaced.  
The replacement is [Metrics](../architecture/metrics.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  
