# Regeltest auf Zusammenfassungen

Diese 20 Fixtures sind **keine Originalinserate**, sondern Zusammenfassungen der Inserate
aus `fixtures/listings/MANIFEST.md` in eigenen Worten (Abruf 12.10.2026, vom Owner
geliefert, ursprünglich mit einem Sprachmodell erstellt). Gegenüber der Lieferung sind
nur die Fettschrift-Markierungen und die Prüfpunkte des Owners entfernt und bei Nr. 4 und
Nr. 11 die Hausnummer gelöscht.

## Was der Regeltest misst – und was nicht

- **Misst:** ob der Skill die Konfliktregeln aus `docs/EXTRACTION_ERRORS.md` einhält
  (Jahres-, Brutto- und Soll-Miete, Preisfeld vs. Text, Flächenschwelle, Fremdwährung,
  Stellplatzmiete) und ob jedes `belegt`-Zitat im Text steht.
- **Misst nicht:** Originalsprache, Originalformate, kyrillische Schrift, PDF-Textschicht.
  Bezeichnungen wie «Wohnfläche» sind Übersetzungen; das Gold folgt dem Wortlaut der
  Zusammenfassung, nicht dem Original.
- Ein grünes Ergebnis hier ist **nicht** das Gate von Stufe 1. Dieses bleibt an
  `fixtures/listings/` mit Originaltexten gebunden.

## Dateien

| Datei | Inhalt | Git |
|---|---|---|
| `<name>.txt` | Zusammenfassung (Quelltext für Zitate) | committet |
| `<name>.gold.json` | Gold nach den Regeln; Grenzfälle vom Owner entschieden (12.10.2026) | committet |
| `<name>.pred.json` | Kandidat des Skills, ohne Kenntnis des Golds erzeugt | ignoriert |

```bash
python scripts/eval_extraction.py fixtures/summaries
```
