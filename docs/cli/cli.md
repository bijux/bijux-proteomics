# cli  

**Scope:** CLI command contract.  
**Audience:** Users and contributors.  
**Guarantees:** Commands listed here are stable.  
**Non-Goals:** Usage examples.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one responsibility.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Core Concepts](../concepts/core_concepts.md) for vocabulary.  
Read [Docs Style](../meta/DOCS_STYLE.md) before edits.  
Read [Cli Surface](../interface/cli_surface.md) for context.  

## Contracts  
Each statement is a contract.  
Contracts align with [packages/agentic-proteins/tests/integration/test_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/integration/test_cli.py).  
Contracts link to [Docs Style](../meta/DOCS_STYLE.md) and [Cli Surface](../interface/cli_surface.md).  

## Invariants  
Invariants describe stable behavior.  
Checks align with [packages/agentic-proteins/tests/integration/test_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/integration/test_cli.py).  
Invariants align with [Docs Style](../meta/DOCS_STYLE.md).  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [packages/agentic-proteins/tests/integration/test_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/integration/test_cli.py).  
Failures align with [Cli Surface](../interface/cli_surface.md).  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Docs Style](../meta/DOCS_STYLE.md).  
Extensions align with [packages/agentic-proteins/tests/integration/test_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/integration/test_cli.py).  

## Exit Criteria  
This doc becomes obsolete when the surface ends.  
The replacement is linked in [Cli Surface](../interface/cli_surface.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/integration/test_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/integration/test_cli.py).  
