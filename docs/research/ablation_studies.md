# ablation_studies  

**Scope:** Ablation study matrix.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Ablations are explicit.  
**Non-Goals:** Full experiment suite.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc lists required ablations.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Claim context lives in [Falsifiable Claim](falsifiable_claim.md).  

## Contracts  
Each ablation removes one capability.  
Ablations compare recovery and failure metrics.  
Metrics follow [Metrics](../architecture/metrics.md).  
Evidence uses [tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/regression/test_negative_results.py).  
| Ablation | Removed capability | Expected signal. |  
| --- | --- | --- |  
| No regulator | Proposal application | Recovery drop. |  
| No stochasticity | Noise in transitions | Variance drop. |  
| No recovery | Failure handling | Recovery drop. |  
| No constraints | Constraint checks | Failure rise. |  

## Invariants  
Ablation list stays fixed.  
List aligns with [Core](../governance/core.md).  
Evidence aligns with [tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/regression/test_negative_results.py).  

## Failure Modes  
Missing ablations weaken claims.  
List drift breaks [Core](../governance/core.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Ablation updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when ablations are encoded.  
The replacement is [Metrics](../architecture/metrics.md).  
Obsolete docs are removed.  

Code refs: [tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/regression/test_negative_results.py).  
