# conservation  

**Scope:** Global conservation checks.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Conservation violations stop execution.  
**Non-Goals:** Biological realism beyond constraints.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines pathway-level conservation checks.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Docs Style](../meta/DOCS_STYLE.md) for structure.  

## Contracts  
Total energy is bounded by a minimum.  
Activation mass is capped per pathway.  
Resource dependencies are validated against a pool.  

## Invariants  
Violations are detected and logged.  
Execution stops on violation.  
Checks apply to every tick.  

## Failure Modes  
Energy violations raise errors.  
Activation mass violations raise errors.  
Resource violations raise errors.  

## Extension Points  
Conservation changes update [Metrics](metrics.md).  
Contract changes update [Pathway Limits](pathway_limits.md).  
Documentation updates follow [Triage](../meta/TRIAGE.md).  

## Exit Criteria  
This doc becomes obsolete when checks are generated.  
The replacement is [Architecture](architecture.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/biology/pathway.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/pathway.py).  
