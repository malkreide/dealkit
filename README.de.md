# dealkit

**Evidenzbasiertes Immobilien-Deal-Screening mit Human Gate.**

🇬🇧 [English version](README.md)

dealkit macht aus einem Inserat und einem Investor-Mandat ein reproduzierbares
Screening-Ergebnis: *pruefen* (vertieft prüfen), *beobachten* (mit expliziten
Triggern) oder *verwerfen*. Es sagt nie «kaufen».

Das Architekturprinzip stammt aus dem Bauplan des Immobilien-Kompass und wird
hier strukturell durchgesetzt:

> **KI extrahiert und erklärt · das Finanzmodell rechnet deterministisch ·
> Regeln entscheiden nachvollziehbar · der Mensch entscheidet.**

## Inhalt

| Baustein | Zweck |
|---|---|
| `schemas/evidence.schema.json` | Jede Angabe trägt einen Status (`belegt / geschaetzt / angenommen / fehlend`) und eine Quellenstufe (`amtlich / portal / makler / …`). |
| `schemas/listing.schema.json` | Objektprofil aus belegten Werten. |
| `schemas/mandate.schema.json` | Investor-Mandat: Märkte, Kapital, Strategie, Limits, Beobachten-Trigger. Alles, was der Kompass fest eingebaut hatte, steht hier. |
| `src/dealkit/model.py` | Deterministische Engine für Finanzierung, Cashflow, Zielpreis, Stresstest und 5/10/15-Jahre-Szenarien. Python-Port von `lib/model.ts`, auf den Euro genau rückgetestet. |
| `src/dealkit/profiles.py` | Marktprofile: DE (Referenz), CH, AL, ME, RS (die letzten vier sind Stubs mit dokumentierten Annahmen). AT, MK, BA, BG, HR sind reine Extraktionsmärkte ohne Profil. |
| `src/dealkit/redflags.py` | Due-Diligence-Checklisten je Markt. Die Engine listet und verfolgt sie; beantworten tun Menschen. Ein `blocker`-Befund überstimmt jeden Score. |
| `src/dealkit/rules.py` | `kompass_v1` (Original-Score und Entscheidungstabelle für Backtests) und `dealkit_v1` (neu gefasste Regeln mit drei harten Übersteuerungen). |
| `src/dealkit/cli.py` | `dealkit validate | screen | checklist | extract | backtest` |
| `src/dealkit/extraction.py`, `scripts/eval_extraction.py` | Extraktions-Gerüst (`dealkit extract`, ohne LLM) und Eval für Stufe 1: Gold gegen Kandidat, Kernwerte ±1 %, Status exakt, jedes `belegt`-Zitat muss im Quelltext vorkommen. Fehlklassen: `docs/EXTRACTION_ERRORS.md`. |
| `skills/deal-screen/` | Claude-Skill, der die Pipeline durchläuft und bei der Vorschau endet. |

## Schnellstart

```bash
pip install -e ".[dev]"
dealkit backtest                                   # reproduziert das Kompass-Rechenbeispiel
dealkit validate examples/listing.leipzig.json     # Schema + Plausibilitäts-Lints
dealkit screen examples/listing.leipzig.json -m examples/mandate.example.yaml
dealkit checklist AL --type wohnung                # Red-Flag-Liste zum Einfügen ins Inserat
dealkit extract fixtures/listings/de-x.txt -o x.json # leeres, schema-valides Objektprofil zum Füllen
python scripts/eval_extraction.py                  # Extraktions-Eval (Stufe 1)
pytest
```

## Die drei harten Regeln

1. **Fehlende kritische Daten verhindern eine positive Empfehlung.** Kaufpreis,
   Wohnfläche und Miete müssen vorliegen; `fehlend` → `daten_vervollstaendigen`.
2. **Schwere Objekt- oder Rechtsrisiken überstimmen einen guten Finanzscore.**
   Ein `blocker`-Befund (Titel, Legalisierung, Restitution …) → `verwerfen`.
3. **Jede Marktaussage hat eine Quelle oder ist als Annahme gekennzeichnet.**
   Durchgesetzt vom Evidenz-Schema; die Bewertung weist den schwächsten Status
   der kritischen Felder aus.

## Was dealkit nicht ist

- Kein Automated Valuation Model (dafür: AlpVal).
- Kein Sourcing-Agent: Portal-Scraping ist bewusst ausserhalb des Scopes (ToS,
  JavaScript, Blockaden). Inserate kommen per URL/PDF oder Portal-E-Mail-Alert.
- Keine Anlageberatung. Scores messen die Passung zu *deinen* Regeln; sie sind
  nicht an Ergebnissen kalibriert. Das Entscheidungs-Log (`docs/ROADMAP.md`,
  Stufe 3) ist der Weg zur Kalibrierung.

## Roadmap

Siehe [docs/ROADMAP.md](docs/ROADMAP.md) – fünf Stufen mit Gates, vom
Engine-Port (Stufe 0, erledigt) bis zum optionalen Always-on-Fetcher auf dem
Raspberry Pi 5 (Stufe 5).

## Verwandte Projekte

- [journeykit](https://github.com/malkreide/journeykit) – Evidenz-Atom-Muster
- [personakit](https://github.com/malkreide/personakit) – das Mandat ist eine Persona
- [swiss-housing-mcp](https://github.com/malkreide/swiss-housing-mcp), [swisstopo-mcp](https://github.com/malkreide/swisstopo-mcp), [swiss-snb-mcp](https://github.com/malkreide/swiss-snb-mcp) – Marktkontext und Wechselkurse für CH-Objekte

## Lizenz

MIT © Hayal Özkan
