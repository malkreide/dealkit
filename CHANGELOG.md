# Changelog

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
