# core_concepts  

**Scope:** Closed vocabulary for core concepts.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Definitions are canonical and enforced.  
**Non-Goals:** Expanded domain theory.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
Core concepts are defined as a closed vocabulary.  
Read [Docs Style](../meta/DOCS_STYLE.md) before edits.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  

## Contracts  
Definitions below are the only canonical wording.  
All docs reference this page for vocabulary.  
Terms are linked when used.  
- agent: An agent is a stateful decision unit that selects a tool and emits actions.  
- tool: A tool is a callable capability used by an agent within an execution unit.  
- policy: A policy is a constraint set that governs agent decisions and tool usage.  
- execution unit: An execution unit is a bounded step that applies a tool and records outputs.  
- evaluation artifact: An evaluation artifact is a stored result from scoring or validation.  
- protein: A protein is a constrained agent with explicit state and constraints.  
- signal: A signal is a typed input that triggers a state transition.  
- pathway: A pathway is a multi-agent system of protein agents.  
- regulation: Regulation is bounded proposal tuning that never mutates state.  
- cell: A cell is an execution environment for pathways.  

## Invariants  
Canonical wording is enforced in [Naming](../meta/NAMING.md).  
Aliases are not used in docs.  
Vocabulary aligns with [Getting Started](../overview/getting_started.md).  
failure semantics align with [Invariants](../architecture/invariants.md).  

## Failure Modes  
Alias usage fails docs lint.  
Unlinked terms fail docs lint.  
Redefinition outside this page fails review.  
recovery semantics align with [Invariants](../architecture/invariants.md).  

## Extension Points  
Change requests follow [Triage](../meta/TRIAGE.md).  
Updates propagate to [Getting Started](../overview/getting_started.md).  
Updates propagate to [Architecture](../architecture/architecture.md).  

## Exit Criteria  
This doc becomes obsolete when vocabulary is generated.  
The replacement is [Architecture](../architecture/architecture.md).  
Obsolete docs are removed.  

Code refs: [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
