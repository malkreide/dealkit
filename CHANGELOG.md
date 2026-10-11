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
