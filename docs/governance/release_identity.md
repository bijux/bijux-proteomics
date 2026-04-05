# release_identity  

**Scope:** Release identity selection.  
**Audience:** Reviewers and contributors.  
**Guarantees:** Identity is explicit.  
**Non-Goals:** Marketing framing.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the release identity.  
Positioning context lives in [Positioning](positioning.md).  
Version context lives in [Semver](semver.md).  

## Contracts  
Release identity is research prototype.  
Identity aligns with [Core](core.md).  
Evidence aligns with [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  

## Invariants  
Identity stays fixed across releases.  
Identity aligns with [Positioning](positioning.md).  
Identity aligns with [Semver](semver.md).  

## Failure Modes  
Ambiguity breaks reviewability.  
Identity drift breaks [Core](core.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  
MPI changes align with [Surface Area](../externalization/surface_area.md).  

## Exit Criteria  
This doc is obsolete when identity is encoded.  
The replacement is [Core](core.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/regression/test_architecture_invariants.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/regression/test_architecture_invariants.py).  
