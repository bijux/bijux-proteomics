# design_debt  

**Scope:** Design debt ledger.  
**Audience:** Contributors.  
**Guarantees:** Ledger contains <=10 items with exits.  
**Non-Goals:** Issue tracking.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines one responsibility.  
Architecture components are defined in [Architecture](architecture.md).  
Read [Triage](../meta/TRIAGE.md) before edits.  
Read [Docs Style](../meta/DOCS_STYLE.md) for context.  

## Contracts  
Each statement is a contract.  
Contracts align with [scripts/check_design_debt.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_design_debt.py).  
Contracts link to [Triage](../meta/TRIAGE.md) and [Docs Style](../meta/DOCS_STYLE.md).  

## Invariants  
Invariants describe stable behavior.  
Checks align with [scripts/check_design_debt.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_design_debt.py).  
Invariants align with [Triage](../meta/TRIAGE.md).  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [scripts/check_design_debt.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_design_debt.py).  
Failures align with [Docs Style](../meta/DOCS_STYLE.md).  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Triage](../meta/TRIAGE.md).  
Extensions align with [scripts/check_design_debt.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_design_debt.py).  

## Exit Criteria  
This doc becomes obsolete when the surface ends.  
The replacement is linked in [Docs Style](../meta/DOCS_STYLE.md).  
Obsolete docs are removed.  

Code refs: [scripts/check_design_debt.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_design_debt.py).  
