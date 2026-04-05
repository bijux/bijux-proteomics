# overview  

**Scope:** HTTP API summary.  
**Audience:** API users.  
**Guarantees:** API mirrors CLI capabilities.  
**Non-Goals:** Authentication.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one responsibility.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Cli](../cli/cli.md) before edits.  
Read [Docs Style](../meta/DOCS_STYLE.md) for context.  

## Contracts  
Each statement is a contract.  
Contracts align with [packages/agentic-proteins/tests/api/test_run.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/api/test_run.py).  
Contracts link to [Cli](../cli/cli.md) and [Docs Style](../meta/DOCS_STYLE.md).  

## Invariants  
Invariants describe stable behavior.  
Checks align with [packages/agentic-proteins/tests/api/test_run.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/api/test_run.py).  
Invariants align with [Cli](../cli/cli.md).  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [packages/agentic-proteins/tests/api/test_run.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/api/test_run.py).  
Failures align with [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Cli](../cli/cli.md).  
Extensions align with [packages/agentic-proteins/tests/api/test_run.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/api/test_run.py).  

## Exit Criteria  
This doc becomes obsolete when the surface ends.  
The replacement is linked in [Docs Style](../meta/DOCS_STYLE.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/api/test_run.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/api/test_run.py).  
