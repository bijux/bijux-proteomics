# DOCS_VOICE  

**Scope:** Documentation voice rules.  
**Audience:** Contributors writing docs.  
**Guarantees:** Voice rules are enforced by CI.  
**Non-Goals:** Copywriting advice.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the documentation voice.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Docs Style](DOCS_STYLE.md) before edits.  
Read [Naming](NAMING.md) for naming context.  

## Contracts  
Tense is present and declarative.  
Person is impersonal and system-centric.  
Sentence length is limited to twenty words.  

## Invariants  
Marketing language is forbidden.  
Opinion and hedging language is forbidden.  
Narrative framing is forbidden.  

## Failure Modes  
Voice violations fail docs lint.  
Voice violations block CI.  
Voice violations require a rewrite.  

## Extension Points  
Voice rules change only in this file.  
Voice changes update [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
Voice changes update [Docs Style](DOCS_STYLE.md).  

## Exit Criteria  
This doc becomes obsolete when docs are generated.  
The replacement is [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
Obsolete docs are removed.  

Code refs: [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
