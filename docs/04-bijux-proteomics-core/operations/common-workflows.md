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

## Peptide Property Screening

Use `peptide-properties` when the question is whether one peptide is sensible
to carry forward into search-space design, targeted review, or downstream
analysis.

- The property report combines monoisotopic mass, average mass, charge-state
  precursor m/z, residue length, protease-specific missed-cleavage count, and
  a simple hydrophobicity proxy in one review object.
- Missed-cleavage counting stays tied to the selected protease rule, including
  custom rules, instead of assuming trypsin silently.
- The hydrophobicity value is a Kyte-Doolittle average proxy, not a retention
  time predictor or chromatographic model.
- Problem flags are heuristic and reviewer-facing. They currently surface short
  peptides, long peptides, high missed-cleavage burden, and strongly
  hydrophobic peptides so filtering decisions remain explicit.

This surface is intentionally honest about scope. It helps triage peptide
candidates before search or analysis, but it does not claim to predict
ionization efficiency, retention time, or identification success directly.

## Fragment-Ion Review

Use `fragment-ions` when the question is whether one peptide has the expected
theoretical b/y fragmentation pattern before moving on to spectrum annotation
or PSM review.

- The surface stays explicit about charge state and can emit both `1+` and `2+`
  fragment ions in one report.
- Neutral losses remain opt-in so reviewers can decide when water, ammonia, or
  modification-specific loss channels should be part of the comparison space.
- Modified peptides are handled through the same owned modification registry
  and canonical peptide contract used elsewhere in the package.
- The report is intentionally separate from spectrum matching so operators can
  inspect the theoretical evidence surface before discussing peak support.
- Curated reference cases validate the generator against known unmodified,
  acetylated, and phosphorylated examples.

This surface is intentionally theoretical. It generates the fragment evidence
space honestly, but it does not claim that any individual fragment is observed
until the later annotation surface matches it to real peaks.

## Precursor Mass-Error Review

Use `precursor-mass-error` when the question is whether observed precursor
assignments are consistent with the claimed peptide identities and charge
states.

- The surface compares observed precursor m/z values against theoretical
  peptide m/z values under the supplied charge state instead of collapsing
  everything to neutral mass.
- Modified peptide notation stays valid input, so theoretical m/z can reflect
  the same owned modification registry used elsewhere in the package.
- The report keeps both Dalton and ppm error visible per observation.
- Isotope-offset review stays advisory and explicit. The command ranks offset
  candidates rather than silently correcting precursor assignments.
- Reviewer-facing summaries include charge distribution, absolute-ppm
  distribution, and recommended isotope-offset distribution across the input
  table.

This surface is intentionally diagnostic rather than corrective. It helps
operators see calibration drift or monoisotopic-assignment problems, but it
does not rewrite the source evidence automatically.

## Search-Engine Modified Peptide Normalization

Use `modified-peptide-parse` when modified peptide strings arrive from
different search engines and the problem is notation drift rather than peptide
chemistry itself.

- The normalization surface accepts MaxQuant, MSFragger, FragPipe, Sage, and
  Comet dialect labels explicitly.
- MaxQuant-style parenthetical modification strings are translated into the
  owned canonical bracket notation, including protein-terminal assignments when
  the engine string states them.
- MSFragger, FragPipe, and Comet bracket-delta dialects are normalized through
  one shared numeric-bracket path because their review burden is the same:
  recover peptide-localized and terminal modification intent into the owned
  contract.
- Sage notation is normalized through the owned bracket parser and then
  canonicalized so known deltas resolve to the stable modification names the
  package already owns.
- The output keeps residue sequence, site positions, terminal context, and the
  final canonical modified peptide string explicit.

This surface is intentionally a notation normalizer, not a search-result
adapter. It turns one engine-specific peptide string into the owned modified
peptide contract so downstream chemistry, PTM, and attribution surfaces do not
need five separate parsers.

## FragPipe Bundle Import

Use `fragpipe-import` when the question is whether one FragPipe export bundle
can be reviewed coherently as PSM, peptide, and protein evidence instead of as
three disconnected TSV files.

- The PSM surface reuses the owned MSFragger normalization machinery through a
  dedicated FragPipe dialect rather than inventing a second PSM parser for the
  same score family.
- The importer keeps the `psm.tsv` row contract explicit, including
  hyperscore, q-value, target-decoy state, protein mapping, assigned or
  observed modifications, and open-search-style mass-difference evidence when
  it is present.
- The peptide table stays separate instead of being flattened into the PSM
  layer, so peptide-level probability, spectral count, mapped proteins, and
  mass-shift evidence remain reviewable in their own right.
- The protein table also stays explicit, preserving protein identity,
  annotation, coverage, peptide burden, spectral count, and probability.
- Modified-peptide notation is normalized through the owned FragPipe peptide
  dialect so residue-localized PTM intent is preserved while the bundle is
  imported.
- The summary surface counts modified rows, q-value coverage, open-search-like
  rows, and mapped proteins so reviewers can spot whether a bundle is a simple
  closed-search export or a more complicated shifted-mass result set.

This surface is intentionally an import and review contract, not a claim that
every FragPipe or Philosopher downstream table is already modeled. It covers
the core PSM, peptide, and protein tables honestly and keeps their evidence
burden explicit for later confidence, PTM, or protein-inference work.

## Sage Import

Use `sage-import` when the question is whether one Sage result table can be
reviewed as explicit identification evidence instead of being flattened into a
single generic PSM score column.

- The import surface keeps Sage discriminant score as the ranking score while
  still preserving hyperscore alongside it for reviewer-facing comparison.
- Modified peptide strings are normalized through the owned Sage peptide
  dialect so stripped residue sequence and canonical modified-peptide intent
  stay explicit.
- Protein mappings remain first-class instead of being reduced to one winning
  accession, so shared evidence and multi-protein rows remain visible.
- The import report keeps q-value, peptide-q-value, protein-q-value, and
  posterior error separate when the export actually carries them.
- Match-shape evidence such as matched peaks, longest b or y series,
  explained-intensity fraction, and mass-accuracy fields remains attached to
  each row instead of disappearing during normalization.
- When a Sage configuration file is available, the same surface also preserves
  enzyme, tolerance, decoy, and modification provenance so the result table can
  be reviewed in the context that produced it.

This surface is intentionally a Sage import and review contract rather than a
full workflow runner. Its job is to preserve the useful evidence already
present in realistic Sage exports so downstream confidence, PTM, and protein
analysis can start from an honest normalized record.

## Comet Import

Use `comet-import` when the question is whether one classic Comet result file
can be reviewed as governed identification evidence instead of being treated as
just another generic score table.

- The import surface accepts either practical pepXML evidence or a realistic
  tabular Comet PSM export through one owned report contract.
- XCorr, DeltaCn, expectation value, and Sp score remain explicit reviewer
  fields instead of being collapsed into one generic ranking number.
- Modified peptide notation is normalized through the owned Comet peptide
  dialect so residue sequence and canonical modified-peptide intent stay
  visible across both input shapes.
- Protein mappings remain explicit, including multi-protein rows and
  target-decoy labels derived from the source evidence rather than guessed
  afterward.
- Optional Comet parameter provenance can be attached to the same import
  report so enzyme, tolerance, and modification settings remain reviewable in
  context.

This surface is intentionally a Comet import and review contract rather than a
search runner. Its job is to preserve the evidence burden already present in
classic Comet exports so downstream confidence, PTM, and protein analysis can
start from an honest normalized record.

## MaxQuant Bundle Import

Use `maxquant-import` when one MaxQuant project needs to stay reviewable as its
native `evidence.txt`, `peptides.txt`, and `proteinGroups.txt` bundle instead
of being flattened into one generic evidence table.

- The evidence surface preserves experiment names, score, posterior error
  probability, protein mappings, reverse state, contaminant state, and native
  modified-peptide notation in one owned review row.
- The importer keeps `peptides.txt` separate from evidence rows so peptide
  intensity, peptide-level score burden, leading razor proteins, and modified
  sequence intent remain explicit in their own table.
- The importer also keeps `proteinGroups.txt` explicit, including majority
  protein identifiers, peptide burden, sequence coverage, only-identified-by-
  site state, and LFQ intensity ledgers per experiment.
- Reverse and contaminant flags remain visible at every table layer instead of
  being collapsed into a single target-only summary.
- When a MaxQuant settings file is available, the same surface preserves
  enzyme, tolerance, decoy-prefix, and modification provenance so project
  review can stay tied to the search assumptions that produced the bundle.

This surface is intentionally a MaxQuant import and review contract rather than
an orchestration wrapper around the original tool. Its job is to keep the
native project evidence honest and structured enough for downstream confidence,
quantification, and protein-analysis work.

## DIA-NN Report Import

Use `diann-import` when one DIA-NN report needs to remain reviewable as
precursor-level DIA evidence instead of being flattened into a generic peptide
or PSM table.

- The precursor surface preserves run and sample columns, q-values, target-
  decoy state, `Precursor.Quantity`, and the corresponding `PG.Quantity`
  carried in the report row.
- Protein-group evidence remains explicit through a separate reviewer-facing
  ledger keyed by protein group together with run and sample context.
- `Protein.Group` and `Protein.Ids` are preserved directly so the report stays
  useful for later DIA-native quantification and protein-group review instead
  of collapsing into one accession string.
- The importer also builds the existing DIA-native precursor and protein-group
  quantity report so identification review stays connected to the package's
  owned DIA quant surfaces.
- When a DIA-NN configuration file is available, the same surface preserves
  enzyme, tolerance, decoy-prefix, and modification provenance so the imported
  report stays tied to the search assumptions that produced it.

This surface is intentionally a DIA-NN import and review contract rather than a
full DIA workflow runner. Its job is to preserve precursor-level DIA evidence,
run/sample context, and quantity burden honestly enough for downstream
quantification and comparison work.

## Spectronaut Report Import

Use `spectronaut-import` when one Spectronaut export table needs to remain
reviewable as precursor-level DIA evidence instead of being reduced to a
generic score table.

- The precursor surface preserves precursor identifier, stripped peptide,
  modified peptide, q-value, confidence score, protein group, protein
  accessions, sample name, run name, `FG.Quantity`, and `PG.Quantity`.
- Modified peptide notation remains explicit through a dedicated review row so
  stripped sequence and modified sequence do not get conflated.
- Protein-group evidence stays separate through a reviewer-facing ledger keyed
  by protein group together with run and sample context.
- The import keeps library-style target-decoy state explicit instead of
  inferring it later from a downstream summary.
- When a Spectronaut settings file is available, the same surface preserves
  digestion, tolerance, library, decoy-prefix, and modification provenance so
  the imported report stays tied to the acquisition-conditioned assumptions
  that produced it.

This surface is intentionally a Spectronaut import and review contract rather
than an attempt to mirror every commercial project artifact. Its job is to
preserve the useful exported precursor and protein-group evidence honestly
enough for downstream DIA comparison and quantification work.

## Generic PSM Mapping

Use `psm-map` when a lab-local or lesser-known search export is still a usable
PSM table, but its column names do not match any owned engine-specific import
surface.

- The mapper requires an explicit YAML or JSON column map instead of guessing
  from header text.
- Required fields stay narrow and stable: spectrum or scan identity, peptide,
  charge, and score. Optional fields cover run identity, modified peptide,
  q-value, protein references, explicit decoy labels, and explicit contaminant
  labels.
- The mapper normalizes accepted rows through the owned generic search-adapter
  path rather than creating a second inconsistent PSM parser.
- Accepted rows land on one canonical PSM schema with explicit run identity,
  spectrum identity, residue-only peptide sequence, canonical modified peptide
  when present, charge, score, q-value, protein references, target-decoy
  label, and contaminant flag.
- Unmapped source columns remain visible in the report so lab-local metadata is
  not silently discarded during normalization.

This surface is intentionally for governed mapping, not heuristic ingestion. If
the operator cannot write a clear column map, the table is under-specified and
should not be normalized as if it were already trusted search evidence.

## PSM Evidence Inspection

Use `psm-inspect` when one normalized or lab-local PSM table needs a direct
quality review before FDR filtering, peptide rollup, or protein inference.

- The inspection surface reports total, accepted, and rejected row counts
  explicitly instead of hiding parser loss inside downstream summaries.
- Score and q-value distributions stay reviewer-facing so unusual score ranges
  or weak-confidence tails are visible before thresholding.
- Charge-state and peptide-length distributions show whether the search result
  shape matches the expected acquisition and digest space.
- Missed-cleavage distributions are computed under an explicit protease instead
  of being guessed from generic peptide text.
- The same command can still export normalized JSONL or TSV evidence and the
  provenance manifest, so review does not fork into a separate incompatible
  surface.

This surface is intentionally descriptive rather than declarative. It helps the
operator understand search-result quality honestly, but it does not replace
later FDR policy, contaminant review, or protein-level inference.

## Peptide Evidence Review

Use `peptide-evidence` when the question is not whether one peptide exists in a
database, but how strong the observed peptide evidence looks after peptide-level
rollup and peptide-level FDR review.

- The surface assigns one primary class per observed peptide: `strong`, `weak`,
  `contaminant`, or `decoy`.
- `strong` is intentionally strict. It currently means the peptide is accepted
  at peptide-level FDR, passes the explicit strong-evidence q-value threshold,
  and is unique across the observed protein references in the input evidence.
- `weak` stays explicit instead of disappearing. Shared peptides, lower-quality
  accepted peptides, and rejected non-decoy peptides all remain reviewable
  under one reviewer-facing class with an explanation string.
- Orthogonal tags preserve the evidence shape separately from the primary
  class: `unique` or `shared`, plus `modified`, `contaminant`, and `decoy`
  where applicable.
- The summary surface keeps accepted versus rejected peptide counts visible
  alongside strong, weak, shared, modified, contaminant, and decoy totals.
- Reviewer-facing TSV ledgers remain available for both the summary and the
  per-peptide review rows when the evidence classification needs to move into
  downstream review or release documentation.

This surface is intentionally observed-evidence-facing rather than
database-uniqueness-facing. A peptide can be `strong` here because it is
uniquely supported by the imported protein references, while a separate peptide
index or database audit may still show broader sequence ambiguity in a larger
search database.

## Target-Decoy Reference Validation

Use `fdr-reference-check` when the question is whether the owned target-decoy
FDR implementation still matches curated known examples after runtime changes.

- The validation surface reuses the same owned FDR engine used by direct PSM
  filtering instead of maintaining a second hand-computed benchmark path.
- Reference cases preserve explicit score orientation, optional threshold, and
  fully labeled target-decoy PSM rows so the proof surface stays readable and
  reproducible.
- Validation rows check ranked cumulative target and decoy counts, FDR, q-value,
  and acceptance state one entry at a time rather than collapsing everything
  into one boolean.
- Case reports keep a reproducibility hash and explicit q-value monotonicity
  status so drift is visible even when a mismatch only appears late in the
  ranking.
- Reviewer-facing summary and entry TSV ledgers are available when the proof
  needs to be attached to a change review or release packet.

This surface is intentionally regression-facing rather than user-facing search
analysis. It proves that the owned target-decoy implementation still behaves
like the curated examples it claims to match, but it does not replace search
result inspection or biological-confidence interpretation.

## Evidence-Level FDR Review

Use `fdr-levels` when the question is how PSM-, peptide-, and protein-level
acceptance diverge at standard confidence cutoffs instead of assuming one level
stands in for the others.

- The review surface compares the owned PSM, peptide, and protein FDR reports
  directly across explicit thresholds rather than leaving that comparison
  implicit inside a larger inference payload.
- Standard thresholds default to 1%, 5%, and 10%, which makes the comparison
  stable and easy to review across runs.
- Each threshold summary keeps total and accepted counts separate so decoy-rich
  or contaminant-heavy evidence cannot disappear behind one accepted-count line.
- Contaminant burden stays visible at every evidence level through explicit
  contaminant counts instead of being flattened into target-only summaries.
- Accepted-entry ledgers stay available so an operator can inspect which
  peptide or protein entities remain after each threshold instead of trusting
  one aggregate table.

This surface is intentionally review-oriented rather than inferential. It helps
operators see why PSM, peptide, and protein confidence differ, but it does not
replace later grouping, picked-protein competition, or biological
interpretation.

## Picked-Protein FDR Review

Use `picked-protein-fdr` when the question is whether target-versus-decoy
protein competition is behaving defensibly before final protein-confidence
interpretation.

- The review surface reuses the owned picked-protein FDR engine instead of
  rebuilding target-versus-decoy pairing logic in a second reporting path.
- Target proteins and their paired decoy partners stay explicit per threshold,
  so the kept-versus-discarded competition remains reviewable instead of being
  flattened into one accepted-protein count.
- Shared-peptide protein-group context stays visible through explicit
  group identifiers on the review entries, which makes ambiguous protein-space
  evidence visible during picked competition rather than only after inference.
- Threshold summaries keep total, accepted, target, decoy, contaminant, and
  grouped-protein burden separate, so one strong target count cannot hide weak
  protein-space structure elsewhere in the report.
- Reviewer-facing summary and entry ledgers remain available when a change,
  release, or search-policy review needs concrete known-example proof instead
  of a generic protein FDR statement.

This surface is intentionally competition-facing rather than biological. It
shows how target and decoy proteins compete under the owned picked-protein
policy, but it does not replace later protein-group interpretation or broader
confidence discussion.

## Protein Grouping Review

Use `protein-groups` when observed peptides already support proteins, but the
question is which proteins remain indistinguishable and which one is only a
stable leading representative inside that group.

- The grouping surface collapses proteins by the exact peptide evidence they
  share instead of reporting every accession as if it were independently
  identified.
- Unique and shared peptide ledgers stay explicit per group, so the operator
  can see whether one group is supported by one protein-specific peptide or
  only by broad shared evidence.
- A deterministic leading protein is reported for each group using the same
  unique-evidence, best-score, then accession tie-break policy used elsewhere
  in the package.
- The leading protein remains a reviewer-facing representative, not a claim
  that the rest of the group vanished biologically.
- Reviewer-facing summary and group-table ledgers remain available so ambiguous
  and singleton groups can be inspected directly before parsimony or later
  confidence interpretation.

This surface is intentionally grouping-facing rather than inferential. It
shows which proteins collapse together under the observed peptide evidence, but
it does not by itself choose the final minimal explanatory protein set.

## Protein Ambiguity Review

Use `protein-ambiguity` when the grouping question is no longer just which
proteins collapse together, but why the ambiguity persists and how much
confidence the ambiguous evidence still carries.

- The ambiguity surface focuses only on unresolved protein groups instead of
  repeating singleton protein rows that are no longer the review problem.
- Indistinguishable members stay explicit as full accession ledgers, so the
  reviewer can see when several proteins are supported by the same observed
  peptide set.
- Shared peptides that create ambiguity stay separate from unique peptides
  that anchor one protein to the group boundary, which prevents one anchored
  singleton from looking identical to a fully indistinguishable pair.
- Outside-group proteins remain explicit when one shared peptide links the
  current group to evidence elsewhere in protein space.
- Group confidence stays reviewer-facing through preserved group q-values plus
  high, medium, low, rejected, or decoy labels, so ambiguity strength is not
  flattened into one generic warning.

This surface is intentionally anti-overclaiming. It explains why one protein
identity cannot be promoted cleanly from the observed peptide evidence, but it
does not pretend to resolve the ambiguity by itself.

## Protein Inference Benchmark Review

Use `protein-inference-benchmarks` when the question is whether the owned
protein-inference logic has actually been exercised against the hard cases that
make protein calls scientifically fragile.

- The benchmark surface ships one named catalog of truth-scored pressure
  scenarios instead of leaving shared-peptide, isoform, homolog-family,
  contaminant, and decoy pressure scattered across test-only helpers.
- Each scenario keeps expected-present and expected-absent proteins explicit,
  so false positive and false negative behavior is reviewable per inference
  strategy rather than hidden inside one aggregate score.
- Strategy assessments preserve precision and recall together with Wilson lower
  bounds, which makes weak-case behavior visible even when one method looks
  acceptable by point estimate alone.
- Reviewer-facing summary, scenario, and assessment ledgers remain available so
  the benchmark surface can travel into operator review or later workflow trust
  decisions without pretending benchmark coverage is broader than it is.
- The current suite intentionally keeps false-negative pressure alongside the
  five requested hard-case families, because conservative under-calling is also
  one real failure mode of protein inference.

This surface is intentionally credibility-facing. It does not invent a new
protein-inference policy; it pressure-tests the owned inference policies
against explicit hard examples before broader claims are promoted.

## Protein Coverage Review

Use `protein-coverage` when the question is not yet which protein set wins the
inference policy, but how much of each protein sequence is directly covered by
accepted peptide evidence.

- The coverage surface maps accepted peptides back onto explicit protein
  sequences instead of inferring sequence coverage only from protein-group
  membership.
- Covered regions stay explicit as stable residue intervals, which makes it
  possible to review whether one protein is supported by one short motif or by
  multiple separated sequence segments.
- Unique and shared peptide ledgers remain separate per protein, so a high
  coverage fraction cannot hide the fact that much of the evidence is shared
  across multiple proteins.
- Peptides assigned to one protein but missing from the supplied FASTA sequence
  stay visible as unmatched rows instead of silently disappearing from the
  report.
- Reviewer-facing summary, per-protein coverage, and region ledgers remain
  available when coverage needs to move into downstream operator review or
  release evidence.

This surface is intentionally sequence-review-facing rather than inferential.
It shows how accepted peptide evidence covers supplied protein sequences, but
it does not decide final protein confidence on its own.

## Protein Coverage Plots

Use `protein-coverage-plot` when one sequence-backed coverage review also needs
one durable plot payload or static rendering surface for operator review.

- The plot surface keeps peptide start and end positions explicit for every
  matched sequence occurrence instead of flattening coverage to one fraction
  per protein.
- Modified peptide notation stays attached to plotted rows, so positional
  evidence does not lose the chemistry that made the peptide distinct.
- Peptide confidence remains visible through preserved peptide-level q-values
  when the source table already carries them, with fallback to owned target-
  decoy filtering when it does not.
- Optional intensity stays attached to plotted positions when the source PSM
  table provides it, so abundance context can travel with the coverage view.
- Reviewer-facing position ledgers plus static SVG or HTML outputs remain
  available when the coverage review needs to move into reports or release
  evidence without claiming a richer interactive UI than the runtime owns.

This surface is intentionally plot-ready rather than interactive. It exports
stable coordinates, confidence, modification state, and optional intensity for
sequence-backed coverage review, but it does not claim a browser-side coverage
application.

## Protein Parsimony Review

Use `protein-parsimony` when the question is which minimal explanatory protein
set should be carried forward from grouped evidence, while still keeping the
remaining ambiguity explicit.

- The parsimony surface reuses the owned greedy and named-variant inference
  policies instead of introducing a second ungoverned minimal-set algorithm.
- Selected proteins keep both their full covered-peptide set and their
  newly-explained peptide set, so reviewers can see what each chosen protein
  actually adds to the explanation.
- Shared peptides that remain covered by more than one selected protein stay
  visible as unresolved ambiguity instead of being flattened into a falsely
  exact protein call.
- Variant-level disagreements also stay explicit, including cases where two
  parsimony policies choose the same final protein set but rank it differently.
- The report distinguishes selected proteins, unexplained peptides, and
  unresolved ambiguity so minimal explanation and residual uncertainty remain
  separate concepts.

This surface is intentionally inferential but still reviewer-facing. It chooses
one minimal explanatory protein set under a named policy, but it does not hide
shared-peptide uncertainty or alternative valid parsimony paths.

## OpenMS Import

Use `openms-import` when one OpenMS result bundle needs to stay reviewable as
native identification evidence plus practical feature-level quant evidence.

- The identification surface reads native `idXML` directly and preserves PSM
  rows with run identity, spectrum reference, peptide sequence, charge, score,
  q-value when the score family supports it, precursor m/z, retention time,
  protein references, and target-decoy state.
- Protein evidence is kept separate from PSM rows so protein-level score and
  target-decoy burden remain visible instead of being flattened into peptide
  summaries.
- Quant evidence is imported through an exported feature table rather than
  pretending full owned `consensusXML` coverage already exists.
- The feature-table surface preserves feature identity, sample identity,
  peptide text, canonical peptide, intensity, protein accessions, charge, m/z,
  retention time, and missing-reason state.
- Accepted and rejected feature-row counts remain explicit so malformed export
  rows do not silently disappear.

This surface is intentionally practical and explicit. It owns native `idXML`
for peptide and protein evidence and exported feature tables for quant review.
It does not yet claim full native `consensusXML` import coverage.

## Strong MGF Parsing

Use the MGF parsing surface when tandem-mass-spectra exchange files need to be
reviewed as spectra evidence rather than treated as opaque search-engine
attachments.

- The parser reads one block at a time instead of loading the full file into
  one `read_text().splitlines()` pass.
- The accepted spectrum contract preserves title, spectrum identifier,
  precursor m/z, precursor charge, retention time, and peak arrays when those
  fields are present.
- Missing optional fields such as title, charge, or retention time do not
  invalidate an otherwise usable spectrum block.
- Retention time can be recovered from either `RTINSECONDS` or
  `RTINMINUTES`, with minute values normalized onto seconds.
- Rejected blocks remain explicit with stable issue codes and raw-block
  context, so malformed spectra are reviewable instead of disappearing.
- The same streaming parser underlies both the full parse report and the
  chunk-aware streaming profile used for larger file review.

This surface is intentionally honest about scope. MGF remains a practical
exchange format for MS/MS peak lists and bounded metadata, not a replacement
for richer instrument-native acquisition provenance.

## Practical mzML Review

Use the mzML review surface when an open-format LC-MS/MS run needs practical
inspection without claiming full vendor-native parity.

- The owned parser reads accepted MS1 and MS2 spectra, precursor assignments,
  retention time, and binary peak arrays into the stable spectrum contract.
- Binary decoding support is reported explicitly, including support for
  zlib-compressed float arrays and explicit refusal of unsupported compression
  or precision settings.
- TIC and BPC chromatogram traces are extracted when the mzML run actually
  carries them, rather than being inferred from spectrum intensities.
- The review surface stays honest when chromatograms are absent. Missing TIC or
  BPC traces are reported as absent, not synthesized.
- The shipped practical fixture proves the parser against one real compressed
  mzML shape with MS1, MS2, precursor context, retention-time normalization,
  and chromatogram traces in one run.

This surface is intentionally practical rather than maximal. It is designed for
reviewable open mzML runs and explicit decoding boundaries, not for pretending
that every vendor-native raw nuance is fully reproduced after conversion.

## Spectrum Annotation

Use `spectrum-annotate` when the question is which observed peaks support one
candidate peptide assignment for one spectrum.

- The annotation surface matches theoretical fragment ions against observed
  peaks under either an explicit Dalton tolerance or an explicit ppm
  tolerance.
- The report keeps the matched-ion rows explicit instead of collapsing them
  into one black-box score.
- Matched-peak count and explained-intensity fraction are part of the owned
  annotation contract, so downstream review surfaces do not need to recompute
  those summary numbers.
- The exported TSV remains the row-oriented evidence table, while the JSON plot
  payload stays dedicated to rendering and inspection.
- The annotation bundle preserves the selected tolerance mode and value
  alongside the raw spectrum, matches, and theoretical fragment set.

This surface is intentionally evidence-facing. It helps reviewers see which
peaks support a peptide assignment, but it does not claim broader search-level
confidence by itself.

## Spectrum Similarity Review

Use `spectrum-similarity` when the question is whether two spectra are
duplicate-like, broadly similar, or the best available match inside a small
reference library.

- The similarity surface computes cosine or dot-product evidence over explicit
  preprocessing modes rather than hiding normalization choices inside one
  opaque score.
- Matching can happen through direct m/z tolerance alignment or through
  reviewer-visible m/z binning, depending on whether the comparison needs
  tight fragment agreement or more library-style coarse matching.
- Duplicate-like and similar labels are reviewer-facing interpretations over
  score, matched-peak count, and explained-intensity fractions. They are not
  search-level confidence claims.
- The ranked library report keeps every candidate row explicit, so operators
  can see where one query spectrum sits among strong, weak, and distinct
  references instead of receiving only one winner.
- Empty or peakless spectra stay explicit as insufficient signal rather than
  being forced into a misleading similarity class.

This surface is intentionally comparative rather than identificatory. It helps
review duplicate spectra, near-neighbor spectra, and lightweight library
matches, but it does not by itself prove peptide correctness or FDR control.

## Spectral-Library Import

Use `spectral-library-import` when the question is whether a practical MSP or
library-shaped MGF file can be imported into an explicit peptide-aware library
contract before running similarity search or DIA-style review.

- The importer supports practical MSP and MGF library inputs rather than
  pretending every library exchange format is already normalized.
- Imported entries preserve peptide identity, precursor m/z, precursor charge,
  fragment peaks, and canonical modified-peptide notation when the library
  entry provides a valid peptide string.
- Explicit decoy labels are preserved when the library metadata states them, so
  later ranked search can distinguish target and decoy competition honestly.
- The importer builds stable peptide and precursor indexes so candidate
  retrieval can happen before full similarity ranking.
- Candidate lookup stays honest: it filters by precursor window and optional
  peptide query, but it does not yet claim full library-search scoring by
  itself.
- Rejected entries remain visible with explicit reasons instead of being
  silently skipped.

This surface is intentionally import-and-index focused. It makes practical
library evidence reviewable and searchable by precursor or peptide, but it does
not yet replace the later ranked search mode.

## Spectral-Library Search

Use `spectral-library-search` when the question is no longer whether a library
imports, but which imported entry is the best explanation for one query
spectrum under an explicit precursor and fragment-matching policy.

- The search surface starts with precursor-window candidate retrieval instead of
  pretending every library entry is equally relevant.
- Candidate spectra are then ranked through the same owned spectrum-similarity
  surface used for pairwise and small-library comparison, so scoring policy
  stays explicit.
- The report exposes the top match directly, but it also keeps the ranked table
  visible so a near-neighbor or decoy competitor cannot disappear behind one
  winner line.
- When imported entries carry explicit decoy labels, the search report keeps a
  concatenated target-decoy strategy visible and fills q-values from that local
  ranking.
- When no decoy evidence is available, the report stays honest and marks the
  search as a no-decoy advisory surface instead of inventing confidence.

This surface is intentionally practical rather than grandiose. It supports
library-style identification or validation over imported MSP or MGF evidence,
but it does not claim a high-scale indexed search engine or a full global
library-FDR calibration model.

## Spectrum Summary Tables

Use the spectrum summary-table surface when the question is run quality and
shape rather than single-spectrum inspection.

- The summary report works across both MGF and mzML accepted spectrum
  contracts.
- mzML summaries preserve reported MS1 versus MS2 counts directly from the
  parsed spectra.
- MGF summaries stay explicit about scope by marking the MS-level policy as an
  MS2 review assumption rather than pretending the file reported MS levels.
- Reviewer-facing tables cover precursor-m/z distribution, precursor-charge
  distribution, retention-time range, and peak-count distribution.
- The summary contract is table-shaped on purpose so operators can review one
  run quickly or export the same ledgers into later QC packets.

This surface is intentionally descriptive rather than inferential. It helps
operators see run structure and burden quickly, but it does not claim a full
instrument-QC diagnosis by itself.

## Spectrum Run QC

Use `spectrum-qc` when the question is whether one raw or exchange-format run
already looks unhealthy before peptide identification or study-level
aggregation.

- The report bins accepted MS/MS spectra over retention time so sparse or
  collapsed acquisition windows stay visible.
- mzML inputs prefer reported TIC and BPC chromatograms when the run actually
  carries them.
- MGF inputs and mzML runs without reported chromatograms still produce
  reviewer-facing TIC and BPC traces derived directly from accepted spectra.
- When precursor intensity is present in the source evidence, the report keeps
  a precursor-intensity burden table instead of hiding that signal.
- Charge-state distribution stays explicit so a run with unexpected precursor
  charge structure can be spotted quickly.
- Empty spectra and low-information spectra are flagged directly rather than
  being averaged away into one summary line.
- The command writes table-shaped ledgers and one plot-ready payload so the
  same QC surface can support review, export, and later report assembly.

This surface is intentionally raw-spectrum QC rather than identification-aware
quality assessment. It helps operators judge LC-MS/MS run health from spectra
alone, but it does not claim peptide-level confidence, calibration
certification, or broader study comparability by itself.

## Unimod-Aware Modification Resolution

Use `modification-resolve` when the question is whether one modification token
is recognized, chemically constrained to the claimed residue, or supplied by a
custom registry rather than the built-in chemistry surface.

- The built-in modification surface resolves durable names, common aliases, and
  controlled identifiers such as `UNIMOD:35`.
- Common review cases now cover oxidation, carbamidomethylation,
  phosphorylation, acetylation, and deamidation without requiring a custom
  registry.
- Residue validation stays explicit. A token can be recognized and still be
  reported as invalid for the claimed residue.
- Unknown modification tokens are returned as reviewer-facing report rows
  rather than being guessed or silently coerced.
- Custom registries remain first-class. A team can supply local or
  institution-specific modification definitions through the existing registry
  document contract and resolve them through the same review surface.

This surface is intentionally a resolution and validation layer, not a promise
that every external search engine or vendor notation is already normalized.
Its job is to make recognized versus unrecognized modification intent explicit
before downstream chemistry or PTM analysis depends on it.

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
