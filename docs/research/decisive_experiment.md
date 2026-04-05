# decisive_experiment  

**Scope:** Decisive experiment design.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Experiment is interpretable.  
**Non-Goals:** Full protocol.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one decisive experiment.  
Architecture context lives in [Architecture](../architecture/architecture.md).  
Claim context lives in [Falsifiable Claim](falsifiable_claim.md).  

## Contracts  
Experiment compares recovery rate with and without regulator proposals.  
Metrics follow [Metrics](../architecture/metrics.md).  
The experiment uses deterministic replay from [Execution Model](../architecture/execution_model.md).  
Evidence uses [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  

## Invariants  
Experiment inputs remain fixed.  
Experiment aligns with [Core](../governance/core.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  

## Failure Modes  
Missing controls breaks interpretation.  
Drift in setup breaks [Falsifiable Claim](falsifiable_claim.md).  
Missing evidence breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Experiment updates follow [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [Experimental](../architecture/experimental.md).  
Evidence updates align with [packages/agentic-proteins/tests/unit/docs/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_docs_contract.py).  

## Exit Criteria  
This doc is obsolete when an experiment suite exists.  
The replacement is [Metrics](../architecture/metrics.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_negative_results.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_negative_results.py).  
