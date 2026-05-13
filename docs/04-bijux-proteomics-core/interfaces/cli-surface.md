---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-13
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py` are the command-line surfaces for core contract workflows
- CLI behavior should reveal contract meaning and validation state rather than runtime orchestration detail
- new CLI promises must stay aligned with the stable contract model

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py`
- `packages/bijux-proteomics-core/tests`

## FASTA Commands

The owned FASTA CLI surface is:

- `fasta-parse`
- `fasta-contaminants`
- `fasta-profile`
- `fasta-stats`
- `fasta-dedup`
- `fasta-filter`
- `fasta-provenance`
- `fasta-decoy`
- `target-decoy-validate`
- `peptide-index`
- `fragment-ions`
- `peptide-properties`
- `precursor-mass-error`
- `modified-peptide-parse`
- `modification-resolve`
- `summarize --kind fasta`

The owned spectrum CLI surface is:

- `spectrum-parse`
- `spectrum-stats`
- `spectrum-annotate`
- `spectrum-similarity`
- `spectral-library-import`
- `spectral-library-search`
- `spectrum-summary`
- `mzml-inspect`
- `summarize --kind mgf`

`fasta-parse` emits the full parser report, including:

- accepted and rejected records
- duplicate identifiers
- duplicate normalized accessions
- parser-level database composition over accepted records

The database composition surface reports:

- accepted record count
- target count
- decoy count
- contaminant count
- accession-namespace counts

`fasta-profile` emits a richer database-review object with:

- a summary block covering input records, accepted proteins, rejected records,
  unique accessions, target count, decoy count, contaminant count, total
  residues, length extremes, and organism annotation coverage
- a stable length-distribution ledger across the bins `1-99`, `100-249`,
  `250-499`, `500-999`, and `1000+`
- an organism-distribution ledger when organism evidence is present in the
  accepted records

`fasta-profile` also supports reviewer-facing TSV exports through:

- `--summary-tsv-out`
- `--length-tsv-out`
- `--organism-tsv-out`

`fasta-contaminants` builds a more realistic search database by:

- appending the owned built-in contaminant panel unless `--no-include-builtin`
  is selected
- appending one or more user-provided contaminant FASTA files through repeated
  `--contaminant-fasta`
- relabeling appended contaminant proteins with the stable `CON__` prefix
- writing a build report with separate built-in and external append counts plus
  skipped duplicate contaminant accessions

`fasta-decoy` builds a target-decoy database and reports both accession-level
and sequence-level review signals.

- `--decoy-mode reverse` and `--decoy-mode shuffle` select the owned decoy
  construction method.
- `--prefix` preserves target protein identity inside the decoy accession while
  enforcing collision-free accession generation.
- Mixed target-plus-decoy inputs are rejected instead of being re-expanded.
- Prefix choices that would collide with existing target accessions fail before
  output is written.

The `fasta-decoy` JSON payload includes:

- `mode`
- `prefix`
- `seed`
- `output_fasta`
- `target_count`
- `decoy_count`
- `report`
- `generation_report`
- `output_sha256`
- `reproducibility_hash`

`generation_report` adds reviewer-facing target-decoy construction details:

- input target count
- generated decoy count
- unchanged sequence count and accession list
- target-sequence collision count and accession list
- validity flag for the generated decoy surface

`target-decoy-validate` checks a finished database after generation and reports:

- target and decoy counts
- prefix and mode compatibility
- duplicate accession and duplicate sequence burden
- target-versus-decoy sequence overlap signals
- overall validity of the target-decoy database

`peptide-index` digests a FASTA database and reports how one or more peptide
queries map back to proteins under the selected digestion assumptions.

- `--peptide` is repeatable and accepts plain or modified peptide notation.
- `--protease`, `--missed-cleavages`, and `--digestion-mode` define the digest
  policy used to build the searchable peptide space.
- `--il-equivalent` optionally collapses isoleucine and leucine during lookup.
- `--protein-group-map` accepts a TSV with `accession` and `protein_group`
  columns so group-specific peptides stay explicit.

The `peptide-index` JSON payload includes:

- input record count
- query peptide count
- protease
- digestion mode
- missed cleavages
- I/L-equivalence flag
- protein-group-map presence flag
- one report object with per-peptide lookup entries and summary counts

Each lookup entry reports:

- the original query peptide
- the canonical residue sequence used for lookup
- the final lookup sequence after optional I/L normalization
- whether modification stripping or I/L-equivalent lookup was applied
- matched protein accessions, families, and groups
- protein-group count
- uniqueness and audit class when the peptide is present
- target, decoy, contaminant, mixed, or missing database membership
- missed-cleavage counts observed among the matching peptide instances
- a reviewer-facing explanation string

`peptide-properties` reports one peptide-level screening object for filtering
or review before search and downstream analysis.

- `--mod` accepts repeatable modification assignments in the same style as
  `peptide-mass`.
- `--charge` chooses the precursor charge state used for m/z calculation.
- `--protease`, `--custom-protease`, and `--custom-protease-name` define the
  missed-cleavage context.
- `--registry` optionally loads a modification registry for named
  modifications.

The `peptide-properties` JSON payload includes:

- canonical notation
- underlying residue sequence
- protease
- charge
- residue length
- monoisotopic mass
- average mass
- monoisotopic precursor m/z for the selected charge state
- missed-cleavage count
- hydrophobicity proxy
- problem flags and a final problematic or not flag

`fragment-ions` emits a dedicated theoretical fragment-ion review report for
one peptide or modified peptide.

- `--mod` accepts repeatable modification assignments in the same style as
  `peptide-mass`.
- `--charge` is repeatable and defaults to both `1` and `2`.
- `--fragment-series` accepts the owned series labels and defaults to `b` plus
  `y`.
- `--include-neutral-losses` adds supported residue and modification losses.
- `--tsv-out` writes one row per theoretical fragment ion.

The `fragment-ions` JSON payload includes:

- canonical notation and residue sequence
- selected charge states and fragment series
- whether neutral losses were included
- total fragment-ion count
- counts by series
- counts by charge
- neutral-loss ion count
- the full fragment-ion rows with series, ordinal, charge, neutral loss, and
  monoisotopic or average mass and m/z values

`precursor-mass-error` emits a reviewer-facing precursor calibration report from
one TSV table of peptide, observed-m/z, and charge observations.

- `--peptide-column`, `--observed-mz-column`, `--charge-column`, and
  `--spectrum-id-column` map the input table.
- `--max-isotope-offset` controls how many isotope-offset candidates are
  ranked.
- `--summary-tsv-out` writes the one-row report summary.
- `--observations-tsv-out` writes one row per peptide observation.
- `--ppm-distribution-tsv-out` writes the absolute-ppm distribution.
- `--charge-distribution-tsv-out` writes the charge-state distribution.
- `--isotope-distribution-tsv-out` writes the recommended isotope-offset
  distribution.

The `precursor-mass-error` JSON payload includes:

- input row count and accepted observation count
- mean and median ppm error plus mean Da error
- median and maximum absolute ppm error
- charge, absolute-ppm, and recommended isotope-offset distributions
- per-observation peptide, canonical peptide, charge, theoretical m/z,
  observed m/z, Da error, ppm error, and isotope advisory
- any requested TSV export paths

`modified-peptide-parse` normalizes one engine-specific modified peptide string
into the owned canonical modified peptide contract.

- `--dialect` is required and accepts `maxquant`, `msfragger`, `fragpipe`,
  `sage`, or `comet`.
- `--registry` optionally loads a modification registry for named
  modifications.
- `--out` writes the normalization report as JSON.

The `modified-peptide-parse` JSON payload includes:

- the named engine dialect
- the original notation
- the stripped residue sequence
- the canonical modified peptide notation
- explicit protein-terminal context flags
- the full normalized modification rows with preserved site positions

`modification-resolve` checks one modification token against the built-in
registry and any optional custom registry supplied at runtime.

- `--residue` optionally asks for residue-compatibility review instead of name
  resolution alone.
- `--registry` loads a JSON modification registry so local or
  institution-specific definitions stay explicit.
- `--out` writes the resolution report as JSON.

The `modification-resolve` JSON payload includes:

- the original query token and normalized token
- whether the token resolved successfully
- builtin, custom-registry, or unknown source classification
- the resolved modification name and controlled identifier when known
- static or variable application class
- allowed site position and residue scope
- monoisotopic and average mass deltas
- optional residue query plus residue-allowed status
- reviewer-facing issues for unknown tokens or residue mismatches

The digestion-oriented CLI surfaces share one protease contract:

- built-in proteases include `trypsin`, `lysc`, `gluc`, `argc`,
  `chymotrypsin`, and `aspn`
- `--custom-protease` accepts explicit rule fragments such as
  `after=KR;block_next=P` or `before=D;block_previous=P`
- `--custom-protease-name` supplies the durable rule name recorded in outputs
- custom protease rules cannot be combined with a second built-in protease name

`spectrum-parse` emits the full MGF parse contract plus a chunk-aware streaming
profile for larger file review.

- `--chunk-size` controls the chunk accounting used in the streaming profile.
- `--accepted-jsonl-out` writes one accepted spectrum object per line.
- `--rejected-json-out` writes the rejected-block ledger as JSON.

The `spectrum-parse` JSON payload includes:

- the full parse report with accepted spectra and rejected blocks
- the compact collection summary
- the streaming profile with chunk size, spectrum count, chunk count, and
  first or last accepted spectrum identifiers
- any accepted-spectrum JSONL or rejected-block JSON export paths

`spectrum-stats` keeps the lighter review surface for one accepted collection:

- summary counts over accepted spectra and rejected blocks
- per-spectrum TIC or base-peak metrics
- a provenance manifest when `--provenance-out` is requested

`spectrum-summary` emits reviewer-facing run summary tables over one MGF or
mzML input.

- `--kind` accepts `auto`, `mgf`, or `mzml`
- `--summary-tsv-out` writes the one-row run summary
- `--charge-tsv-out` writes the precursor-charge distribution
- `--precursor-tsv-out` writes the precursor-m/z distribution
- `--peak-count-tsv-out` writes the peak-count distribution

The `spectrum-summary` JSON payload includes:

- source kind
- ms-level policy
- total, rejected, MS1, MS2, and unknown-ms-level counts
- retention-time minimum and maximum when available
- charge, precursor-m/z, and peak-count distributions
- any requested TSV export paths

`spectrum-qc` emits raw-spectrum run-QC ledgers over one MGF or mzML input.

- `--kind` accepts `auto`, `mgf`, or `mzml`
- `--time-bin-seconds` sets the MS/MS-count retention-time bin width
- `--summary-tsv-out` writes the one-row run-QC summary
- `--msms-tsv-out` writes the MS/MS-count-over-time table
- `--tic-tsv-out` writes the TIC trace table
- `--bpc-tsv-out` writes the BPC trace table
- `--charge-tsv-out` writes the precursor-charge distribution
- `--precursor-intensity-tsv-out` writes the precursor-intensity distribution
- `--flagged-tsv-out` writes the empty and noisy spectrum table
- `--plot-out` writes one plot-ready JSON payload for downstream rendering

The `spectrum-qc` JSON payload includes:

- source kind and chromatogram source
- total, rejected, and MS/MS spectrum counts
- precursor-intensity observation count
- empty-spectrum count and noisy-spectrum count
- MS/MS-count-over-time bins
- TIC and BPC traces
- charge and precursor-intensity distributions
- flagged spectrum rows
- reviewer-facing diagnostics when retention-time or precursor-intensity
  evidence is incomplete
- any requested TSV or plot export paths

`spectrum-annotate` emits one matched-fragment review object plus a plot-ready
payload for one accepted MGF spectrum.

- `--peptide` is required and accepts the owned peptide notation surface.
- `--spectrum-id` optionally selects one accepted spectrum by identifier.
- `--tolerance-da` and `--tolerance-ppm` select the fragment-match tolerance
  mode.
- `--tsv-out` writes the matched-ion evidence table.
- `--plot-out` writes the plot-ready JSON payload.

The `spectrum-annotate` JSON payload includes:

- the full annotation object
- explicit matched-ion rows
- matched-peak count
- explained-intensity fraction
- unmatched-peak count
- the selected tolerance unit plus tolerance value
- ambiguity warnings when one fragment matches multiple peaks or one peak
  matches multiple fragments
- one plot-ready payload with labeled peaks

`spectrum-similarity` compares one accepted query spectrum against either one
selected reference spectrum or an accepted spectrum library from MGF or mzML.

- `--query-kind` and `--reference-kind` accept `auto`, `mgf`, or `mzml`.
- `--query-spectrum-id` optionally selects one accepted query spectrum by
  identifier.
- `--reference-spectrum-id` switches the command into explicit pairwise
  comparison against one selected reference spectrum.
- `--method` accepts `cosine` or `dot_product`.
- `--mode` accepts `raw`, `normalized`, `top_n`, or `transformed`.
- `--tolerance-da` enables direct fragment matching by mass tolerance.
- `--bin-width-da` enables coarse m/z-binned comparison instead of
  tolerance-based matching.
- `--max-matches` limits the ranked library output.
- `--tsv-out` writes the ranked candidate table.

The `spectrum-similarity` JSON payload includes:

- an optional pairwise comparison report when `--reference-spectrum-id` is
  supplied
- a ranked library report for the selected query spectrum
- the explicit preprocessing and matching parameters
- matched-peak count plus explained-intensity fractions
- reviewer-facing classifications such as `duplicate_like`, `similar`,
  `distinct`, or `insufficient_signal`
- any requested TSV export path

`spectral-library-import` imports one practical MSP or library-shaped MGF file
into an explicit peptide-aware library contract.

- `--kind` accepts `auto`, `msp`, or `mgf`.
- `--precursor-mz` optionally runs candidate retrieval against the imported
  precursor index.
- `--tolerance-da` sets the precursor candidate window.
- `--peptide` optionally narrows candidate retrieval to one peptide query.
- `--summary-tsv-out` writes a compact one-row library summary.
- `--candidates-tsv-out` writes the precursor-compatible candidate table and
  requires `--precursor-mz`.

The `spectral-library-import` JSON payload includes:

- the full import report with accepted and rejected entries
- a compact summary over entry count, unique peptides, modified entries, decoy
  entries, and charge distribution
- compact index facts, including peptide lookup content and precursor-index
  size
- an optional candidate report over precursor and peptide-filtered entries
- any requested summary or candidate TSV export paths

`spectral-library-search` ranks one selected query spectrum against one
practical MSP or MGF library.

- `--query-kind` accepts `auto`, `mgf`, or `mzml`.
- `--library-kind` accepts `auto`, `msp`, or `mgf`.
- `--query-spectrum-id` optionally selects one accepted query spectrum by
  identifier.
- `--precursor-tolerance-da` sets the precursor candidate window before any
  similarity scoring happens.
- `--tolerance-da` sets the fragment-matching tolerance for the similarity
  stage.
- `--bin-width-da` optionally switches the similarity stage onto coarse m/z
  binning.
- `--method` accepts `cosine` or `dot_product`.
- `--mode` accepts `raw`, `normalized`, `top_n`, or `transformed`.
- `--top-n` optionally limits preprocessing to the most intense peaks.
- `--max-matches` limits the ranked output table.
- `--tsv-out` writes the ranked match table with target-decoy label, score,
  explained-intensity fractions, and optional q-value.

The `spectral-library-search` JSON payload includes:

- the imported library report used for search
- a compact library summary that keeps decoy-entry count explicit
- one search report with precursor policy, similarity policy, candidate count,
  decoy-candidate count, and ranked matches
- the top-match identifier, peptide, score, and q-value when available
- a search strategy field that stays explicit as either `concatenated` or
  `no_decoy_advisory`
- any requested ranked-TSV export path

`mzml-inspect` reports one practical mzML review object without claiming full
vendor-native replacement.

- `--spectra-jsonl-out` writes accepted spectra as normalized JSONL.
- `--chromatograms-json-out` writes the extracted chromatogram report as JSON.
- the command reports decoding support and chromatogram presence explicitly
  instead of assuming every mzML file is equally supported

The `mzml-inspect` JSON payload includes:

- run metadata
- the compact accepted-spectrum summary
- binary decoding support with accepted and rejected spectrum counts
- extracted chromatogram traces, including TIC and BPC when present
- reviewer-facing diagnostics about practical scope and missing chromatograms
- any accepted-spectrum JSONL or chromatogram JSON export paths

`digest` and `peptide-index` both report:

- the resolved protease name
- the custom protease specification when one was supplied
- the digestion mode
- the missed-cleavage allowance

`digest` exports one theoretical peptide database under the selected digestion
policy.

- `--format` accepts `tsv`, `jsonl`, `parquet`, or `fasta`.
- `--out` writes the main peptide export.
- `--manifest-out` writes the digestion policy manifest.
- `--peptide-protein-table-out` optionally writes a peptide-to-protein TSV
  sidecar with one row per peptide occurrence.

The main peptide exports preserve:

- source accession and source identifier
- peptide sequence
- peptide length
- start and end coordinates
- missed-cleavage count
- protease and digestion mode
- cleavage type
- neutral mass

The peptide FASTA export writes the peptide sequence body and records source
coordinates, missed-cleavage count, peptide length, neutral mass, and protease
in the header.

The peptide-to-protein sidecar preserves:

- peptide sequence
- peptide length
- neutral mass
- source accession and source identifier
- source protein family and isoform
- start and end coordinates
- missed-cleavage count
- protease, digestion mode, and cleavage type

`fasta-stats` reports FASTA-wide review metrics such as duplicate accession
count, duplicate sequence count, target count, decoy count, contaminant count,
and sequence-length summary values.

`summarize --kind fasta` returns the higher-level FASTA summary, the parser-level
database composition, and the richer FASTA profile so operators can distinguish
structural file quality from biological database makeup and annotation burden.

For PSM evidence, the contaminant-review surface is:

- `psm-contaminants`

`psm-contaminants` emits a separate contaminant-match report with:

- contaminant PSM count
- pure-contaminant versus mixed-reference PSM counts
- contaminant peptide count
- contaminant protein counts
- row-level entries listing contaminant and target protein references for each
  contaminant-carrying match

`summarize --kind psm` now includes the same contaminant report alongside the
standard PSM, peptide, and protein summaries.
