---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-13
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- review a program or target contract change against lifecycle and execution rules
- check whether runtime consumers need explicit downstream validation
- update contract-facing docs with the same discipline as the code change

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`

## FASTA Intake

Use the FASTA intake surface before digestion, target-decoy preparation, or
search-database review whenever a protein database may contain mixed header
styles, contaminants, decoys, or lab-local records.

- `fasta-parse` returns accepted and rejected records, duplicate identifiers,
  duplicate normalized accessions, and parser-level database composition.
- Empty-sequence records are rejected explicitly instead of aborting the whole
  file.
- UniProt, RefSeq, Ensembl, and custom lab headers can coexist in one parse
  report.
- Target-decoy and contaminant-heavy databases remain reviewable because the
  accepted-record composition reports target, decoy, and contaminant counts.

The parser contract is intentionally stricter than a line reader. Its job is
to tell the operator whether the database is usable for downstream proteomics
work, not just whether the file is syntactically FASTA-like.

## FASTA Database Profiling

Use `fasta-profile` when the question is not just whether a database parses,
but what kind of search or digestion burden it will create.

- The profile summary reports total input records, accepted proteins, rejected
  records, unique accessions, target count, decoy count, contaminant count,
  and organism annotation coverage.
- The length-distribution ledger bins proteins into stable ranges so long-form
  sequence burden is visible before digestion or search.
- The organism-distribution ledger aggregates proteins by parsed organism name
  when the header carries that evidence.
- The profile can be exported as one JSON object plus dedicated TSV ledgers for
  summary, length distribution, and organism distribution.

This profiling surface is intentionally reviewer-facing. It helps operators
decide whether a database is appropriately scoped and annotated before they
commit to downstream evidence generation.

## Contaminant Database Assembly

Use `fasta-contaminants` when a target-only FASTA is not realistic enough for
search or digestion review on its own.

- The owned built-in contaminant panel appends common carryover proteins such
  as albumin, trypsin, and keratins.
- External contaminant FASTA files can be appended in the same run for
  lab-local contaminants.
- Appended contaminant proteins are relabeled with the stable `CON__` prefix so
  downstream search evidence can distinguish them from targets.
- The build report separates built-in versus external contaminant counts and
  records skipped duplicate contaminant accessions.

After search import, use the contaminant-match review surface to separate
contaminant-carrying PSMs from target-only evidence instead of letting those
matches disappear into the general peptide summary.

## Target-Decoy Database Preparation

Use `fasta-decoy` when a target database is ready for search-space expansion
and the question becomes whether the decoy construction is defensible rather
than merely reproducible.

- Reverse and shuffle decoy modes are both supported through one owned surface.
- Input databases must be target-only. Mixed target-plus-decoy input is
  rejected instead of silently generating a second decoy layer.
- Generated decoy accessions preserve the source protein identity through a
  stable operator-chosen prefix such as `DECOY_`.
- Prefix choices that would collide with existing target accessions are refused
  before output is written.
- The generation report makes sequence-level caveats visible, including decoys
  that are unchanged from their targets and decoys whose sequence content
  collides with target sequence content.

Shuffle decoys are useful only when operators review these caveats honestly.
Low-complexity proteins can yield unchanged or target-colliding sequences even
when the accession-level labeling is correct.

## Peptide Database Indexing

Use `peptide-index` when the question is whether one peptide sequence can
support one protein, several proteins, one protein group, or only contaminant
or decoy hypotheses under a specific digestion policy.

- The lookup report is built from a real digest of the supplied FASTA, not from
  naive substring search across whole proteins.
- Missed-cleavage settings change the searchable peptide space and are recorded
  explicitly.
- Modified peptide notation is reduced to the underlying residue sequence for
  database lookup instead of being treated as a second protein-space alphabet.
- Optional I/L-equivalent lookup makes leucine or isoleucine ambiguity visible
  instead of hiding it inside ad hoc downstream matching.
- Optional protein-group mapping lets one peptide remain shared at the protein
  level while still being specific to one indistinguishable group.
- Database membership remains explicit: target-only, decoy-only,
  contaminant-only, mixed, or missing.

This surface is reviewer-facing on purpose. A peptide can be biologically
interesting and still be weak for protein attribution if it only appears under
decoy, contaminant, or broad shared-peptide conditions.

## Protease-Governed Digestion

Use the digestion surface when peptide-space generation needs to stay explicit
about cleavage assumptions instead of being treated as a black-box
preprocessing step.

- Built-in proteases now cover trypsin, Lys-C, Glu-C, Arg-C, chymotrypsin, and
  Asp-N.
- Blocked-cleavage behavior is part of the rule contract rather than an
  undocumented implementation detail.
- Semi-specific and non-specific digestion remain available when the peptide
  search space must be widened intentionally.
- Custom proteases use an explicit rule string such as
  `after=KR;block_next=P` or `before=D;block_previous=P`.
- Custom rules should be named deliberately because that name survives into the
  digestion manifest and downstream review surfaces.

The digestion contract is honest about scope: a peptide list is only as
defensible as the protease rule and specificity mode that generated it.

## Digestion Export Review

Use `digest` when the peptide space itself needs to be handed off for search,
inspection, or downstream reuse instead of staying trapped inside one runtime
object.

- TSV export writes one peptide occurrence per row with source accession,
  source identifier, coordinates, missed-cleavage count, protease, digestion
  mode, peptide length, and neutral mass.
- FASTA export writes one peptide occurrence per entry and preserves the source
  coordinate plus digestion facts in the header.
- `--peptide-protein-table-out` writes a second reviewer-facing TSV that keeps
  the peptide-to-protein mapping explicit instead of forcing later tools to
  reverse-engineer it.
- The peptide-to-protein table preserves source accession, source family,
  isoform, coordinates, missed-cleavage count, length, and neutral mass for
  each peptide occurrence.
- The manifest and output fingerprint still bind the digestion policy to the
  exported peptide content, so the export remains reviewable as evidence rather
  than just a convenience file.

This export surface is intentionally occurrence-based. Shared peptides appear
once per source protein context so peptide reuse across proteins stays visible
instead of being collapsed away.
