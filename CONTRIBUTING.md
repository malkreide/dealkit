# Contributing

- Every number that enters the valuation must be an evidenced value (`schemas/evidence.schema.json`).
- Changes to `src/dealkit/model.py` must keep `dealkit backtest` green; if the Kompass model is
  intentionally extended, add the new quantity next to the existing ones, do not change them.
- Market profile defaults are assumptions: cite the source in the profile's `notes` when you change one.
- Run `pytest` and `ruff check src tests` before opening a pull request.
- Swiss German spelling in German texts (ss, not ß).
