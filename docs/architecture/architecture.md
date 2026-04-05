# architecture  

**Scope:** Architecture single source of truth.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Diagram and narrative are canonical.  
**Non-Goals:** Alternative diagrams or component redefinitions.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
Architecture components are defined here and referenced elsewhere.  
Read [Core Concepts](../concepts/core_concepts.md) for vocabulary.  
Read [Docs Style](../meta/DOCS_STYLE.md) for structure.  

## Contracts  
The diagram below is the single source of truth.  
The narrative below defines component roles.  
Other docs reference this page for components.  
Diagram: CLI -> runtime control <- API -> providers -> artifacts -> evaluation artifact.  
CLI and API submit requests to runtime control, which coordinates providers and writes artifacts.  

## Invariants  
Runtime control records each execution unit.  
Providers are isolated from runtime control state.  
Artifacts are immutable after write.  

## Failure Modes  
Component drift creates inconsistent behavior.  
Missing references cause documentation mismatch.  
Broken links invalidate the diagram contract.  

## Extension Points  
Architecture changes update [Invariants](invariants.md).  
Architecture changes update [Execution Model](execution_model.md).  
Architecture changes update [Execution Lifecycle](execution_lifecycle.md).  

## Exit Criteria  
This doc becomes obsolete when architecture is generated.  
The replacement is [Invariants](invariants.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/tests/e2e/test_runtime_flow.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/tests/e2e/test_runtime_flow.py).  
