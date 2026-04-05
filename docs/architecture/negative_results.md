# negative_results  

**Scope:** Negative results criteria.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Failure scenarios are explicit and tested.  
**Non-Goals:** Success narratives.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines negative results scenarios.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Metrics](metrics.md) for measurement context.  

## Contracts  
A cyclic pathway must fail validation.  
A proposal that increases energy cost must worsen stability.  
Degraded proteins must not recover.  

## Invariants  
Negative results are enforced by tests.  
Failures are structured and observable.  
No hidden recovery is allowed.  

## Failure Modes  
Silent success invalidates results.  
Missing failures invalidate tests.  
Undefined scenarios are rejected.  

## Extension Points  
Scenario changes update [Metrics](metrics.md).  
Contract changes update [Pathway Limits](pathway_limits.md).  
Documentation updates follow [Triage](../meta/TRIAGE.md).  

## Exit Criteria  
This doc becomes obsolete when results are generated.  
The replacement is [Metrics](metrics.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  
