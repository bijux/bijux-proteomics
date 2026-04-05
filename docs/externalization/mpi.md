# mpi  

**Scope:** Minimal public interface (MPI).  
**Audience:** External users and contributors.  
**Guarantees:** Entry points and contracts are fixed.  
**Non-Goals:** Full API inventory.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc lists the MPI entry points.  
MPI scope aligns with [Core](../governance/core.md).  
Usage context lives in [Golden Path](golden_path.md).  

## Contracts  
Entry point: [CLI](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/interfaces/cli.py). Input is CLI arguments. Output is exit status and workspace artifacts.  
Entry point: [RunManager](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/runtime/control/execution.py). Input is a run directory and config. Output is a run result mapping.  
Entry point: [PathwayExecutor.step](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/pathway.py). Input is a list of [SignalPayload](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/signals.py). Output is a list of SignalPayload.  
Entry point: [ProteinAgent.apply_signal](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/protein_agent.py). Input is a SignalPayload plus ProteinConstraints and ProteinState. Output is a ProteinState.  
Entry point: [SignalPayload](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/biology/signals.py). Input is typed fields (source_id, targets, signal_type via SignalType, magnitude). Output is a validated payload instance.  
Intentionally inaccessible: runtime control, execution runtime, and registry internals.  

## Invariants  
MPI size is capped by [Surface Area](surface_area.md).  
MPI meaning aligns with [Core Concepts](../concepts/core_concepts.md).  
MPI changes require [Invariants](../architecture/invariants.md).  

## Failure Modes  
MPI expansion breaks [Surface Area](surface_area.md).  
Hidden entry points break [Core](../governance/core.md).  
Unlinked usage breaks [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extension rules live in [Experimental](../architecture/experimental.md).  
Playground usage is described in [Sandbox](sandbox.md).  
Review rules align with [Triage](../meta/TRIAGE.md).  

## Exit Criteria  
This doc is obsolete when MPI is generated.  
The replacement is [Surface Area](surface_area.md).  
Obsolete docs are removed.  

Code refs: [packages/agentic-proteins/src/agentic_proteins/core/surface_area.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/core/surface_area.py).  
