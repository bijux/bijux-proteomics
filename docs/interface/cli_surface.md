# cli_surface  

**Scope:** CLI surface list.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Surface list matches click definitions.  
**Non-Goals:** Usage examples.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one responsibility.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Cli](../cli/cli.md) before edits.  
Read [Docs Style](../meta/DOCS_STYLE.md) for context.  

## Contracts  
Each statement is a contract.  
Contracts align with [packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py).  
Contracts link to [Cli](../cli/cli.md) and [Docs Style](../meta/DOCS_STYLE.md).  
- api  
- api serve  
- compare  
- export-report  
- inspect-candidate  
- reproduce  
- resume  
- run  
- --artifacts-dir  
- --dry-run  
- --execution-mode  
- --fasta  
- --host  
- --json  
- --no-docs  
- --no-logs  
- --output  
- --port  
- --pretty  
- --provider  
- --reload  
- --rounds  
- --sequence  

## Invariants  
Invariants describe stable behavior.  
Checks align with [packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py).  
Invariants align with [Cli](../cli/cli.md).  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py).  
Failures align with [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Cli](../cli/cli.md).  
Extensions align with [packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py).  

## Exit Criteria  
This doc becomes obsolete when the surface ends.  
The replacement is linked in [Docs Style](../meta/DOCS_STYLE.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/unit/docs/test_cli_surface_documentation.py).  
