Place raw listing texts here (gitignored). Gold files *.gold.json are committed.

## Naming

| File | Content | Git |
|---|---|---|
| `<name>.txt` or `<name>.pdf` | Raw listing text / exposé (a `.txt` wins over a `.pdf` of the same name) | ignored |
| `<name>.gold.json` | Hand-made, schema-valid `listing.json` – the expected extraction | committed |
| `<name>.pred.json` | Candidate from the deal-screen skill | ignored |

`<name>` starts with the market prefix `de-`, `al-` or `ch-` (also `me-`, `rs-`), e.g.
`de-leipzig-reudnitz-01`.

## Workflow

```bash
dealkit extract fixtures/listings/de-leipzig-reudnitz-01.txt --type wohnung \
  --out fixtures/listings/de-leipzig-reudnitz-01.pred.json    # scaffold, no LLM
# … the deal-screen skill fills the scaffold …
python scripts/eval_extraction.py --min-rate 0.9              # stage-1 gate
```

## Rules for gold files

- Follow `docs/EXTRACTION_ERRORS.md` – the eval compares status exactly.
- No personal data of private sellers: no names, phone numbers or e-mail addresses, neither
  in quotes nor in notes. The eval warns (`pii_verdacht`) but cannot detect names.
- Quotes verbatim from the `.txt`/`.pdf`; a gold quote that cannot be found makes the eval
  exit with code 2.
