# semver  

**Scope:** Semantic version meaning.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Version semantics are explicit.  
**Non-Goals:** Release tooling.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines semantic version meaning.  
Version meaning aligns with [Core](core.md).  
Release history is tracked in [../CHANGELOG.md](https://github.com/bijux/bijux-proteomics/blob/main/CHANGELOG.md).  

## Contracts  
MAJOR means semantic model change.  
MINOR means new capability without meaning shift.  
PATCH means bug fix only.  

## Invariants  
Version changes align with [Invariants](../architecture/invariants.md).  
Contract locks align with [packages/agentic-proteins/src/agentic_proteins/core/api_lock.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/api_lock.py).  
Checks align with [packages/agentic-proteins/tests/unit/core/test_core_api_lock.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/core/test_core_api_lock.py).  

## Failure Modes  
Meaning drift breaks [Core](core.md).  
Mismatched versions break [../CHANGELOG.md](https://github.com/bijux/bijux-proteomics/blob/main/CHANGELOG.md).  
Untracked changes break [Invariants](../architecture/invariants.md).  

## Extension Points  
Extensions follow [Experimental](../architecture/experimental.md).  
Extension checks align with [packages/agentic-proteins/tests/unit/governance/test_module_stability.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/governance/test_module_stability.py).  
Extension docs align with [Docs Style](../meta/DOCS_STYLE.md).  

## Exit Criteria  
This doc is obsolete when versioning is generated.  
The replacement is [Docs Style](../meta/DOCS_STYLE.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/core/api_lock.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/api_lock.py).  
