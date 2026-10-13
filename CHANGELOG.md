# Changelog

## 0.2.0-dev – unreleased

Stage 1 of the roadmap: extraction with provenance – eval harness.

- `scripts/eval_extraction.py`: compares `fixtures/listings/<name>.pred.json` with
  `<name>.gold.json` and the source text (`.txt`, or `.pdf` via pypdf). Core values ±1 %,
  status exact, every `belegt` quote must occur in the source (whitespace-normalised).
  Prints a table per fixture, the overall rate and the error classes. Exit code 1 on a hard-gate
  violation (or with `--min-rate` below the threshold), 2 on missing fixtures or a broken gold
  file; `--json` for machine-readable output.
- `dealkit extract <file> --out <pred.json>`: schema-valid scaffold without any LLM – id, market
  from the file-name prefix, captured_at, source, red-flag checklist (`offen`), every core and
  object field `fehlend`. Refuses to overwrite without `--force`.
- `src/dealkit/extraction.py`: scaffold, comparison and report logic (importable, tested).
- `docs/EXTRACTION_ERRORS.md`: expected error classes (price range, warm vs. cold rent, annual
  rent, project pages, gross vs. net area, Albanian listings, …) with the rule the skill follows.
- Skill `deal-screen`: warm and annual rent now → `fehlend` + note (was `geschaetzt`), in line
  with the roadmap; starts from the `dealkit extract` scaffold; quotes verbatim in the original
  language.
- Optional extra `pdf` (pypdf); `*.pred.json` fixtures are gitignored.
- Tests with synthetic mini-fixtures under `tests/data/extraction/`.
- Extraction-only markets AT, MK, BA, BG, HR (ADR 10): accepted by the listing schema, the scaffold
  and the eval; `dealkit screen` refuses them with a clear message. Currencies BAM and MKD.
- Eval compares `core.currency` (`waehrung_abweichung`): a price in the wrong currency is wrong.
- `fixtures/listings/MANIFEST.md`: the 20 selected listings with file names and source links
  (texts still to be supplied); error classes 14–16 and a coverage section in `EXTRACTION_ERRORS.md`.
- `fixtures/summaries/`: rule test on the owner's summaries of the 20 listings (not original texts,
  so not the stage-1 gate): 20 source texts and gold files; edge cases decided by the owner.
  New rules: area field vs. text within 5 % is no conflict; price field vs. text always is;
  unqualified «Fläche» counts as living area except in AL/BG; rent of a co-sold parking space
  counts; «Miete» without cold/warm is `belegt` with a note; the stricter rule wins.
- CI checks that every committed gold file is schema-valid and its quotes occur in its source.
- Original listing texts fetched on 13.10.2026 (one request per URL, no bot-protection bypass):
  12 of 20 usable; immowelt and ImmoScout24.de (all six DE listings) answer with bot protection,
  two listings have expired. `MANIFEST.md` records status, portal language and redactions per listing.
- New rules from the owner's edge-case decisions on original texts: a data field within 5 % of the
  text wins even when it is visibly rounded; unqualified area labels in other languages («Area»,
  «Floor area», «Površina») count as living area outside AL/BG; quotes follow the fetched portal
  language version including its labels and number format; a separately stated commission goes
  into the note; AT owner costs («Monatliche Kosten», «Betriebskosten») and portal calculators
  (loan rate, computed price per m², class 17) are never rent.
- Gold for the 12 usable original listings (`fixtures/listings/*.gold.json`). Blind candidate
  from a separate agent (rules, schemas and texts only): 12/12 correct, core values 36/36, hard
  gate OK, no warnings; a counter-check with three planted errors (converted annual rent, invented
  quote, wrong currency) is fully detected. Formally the stage-1 gate is met, but it is **not
  robust**: 12 instead of ≥ 18 fixtures, no DE, no CH and no listing with a rent; three rules were
  sharpened on the same set. Result and limits in `docs/EXTRACTION_ERRORS.md` («Ergebnisse»).

## 0.1.0 – 2026-10-10

- Initial skeleton (stage 0 of the roadmap).
- JSON schemas: evidence, listing (Objektprofil), mandate.
- Deterministic engine ported from the Immobilien-Kompass (`lib/model.ts`); backtest reproduces
  all values of the worked example (financing, cash flow, target price, stress, 5/10/15-year
  scenarios).
- Market profiles DE (reference) and CH/AL/ME/RS (stubs with documented assumptions).
- Red-flag catalogue per market; blocker findings override the score.
- Rules: `kompass_v1` (backtest) and `dealkit_v1` (pruefen / beobachten / verwerfen).
- CLI `dealkit validate | screen | checklist | backtest`; Claude skill `deal-screen`.
