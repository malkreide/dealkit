---
name: deal-screen
description: Evidenzbasiertes Immobilien-Deal-Screening mit dealkit. Verwenden, wenn der User ein Inserat (URL, PDF-Exposé, Text) bewerten lassen will, ein Objekt in die Deal-Pipeline aufnehmen möchte, nach «Screening», «Objektprofil», «Zielpreis», «Beobachten-Trigger» oder «Red-Flag-Check» fragt, oder der wöchentliche «Deal-Lauf» ansteht. Nicht für Portfoliobewertung (AVM), nicht für Steuerberatung, nie für Kaufentscheide – der Skill endet immer bei der Vorschau.
---

# deal-screen

Pipeline: **Mandat → Extraktion mit Provenienz → `dealkit screen` → Red-Flag-Review → Vorschau**.
Die KI extrahiert und erklärt; das Finanzmodell rechnet deterministisch; Regeln entscheiden
nachvollziehbar; der Mensch entscheidet. Dieser Skill schreibt nie «kaufen».

## Voraussetzungen

- `dealkit` installiert (`pip install -e .` im Repo) oder Repo-Pfad bekannt.
- Mandat-Datei (`examples/mandate.example.yaml` als Vorlage). Pfad in `config.yml`
  (gitignored) unter `mandate:`; Notion-IDs der Deal-Pipeline-DB ebenfalls dort – nie im SKILL.md.

## Ablauf

### 1. Eingabe entgegennehmen
URL, PDF, Screenshot oder eingefügter Text. Bei URL: Seite abrufen (WebFetch) – wenn das
Portal blockiert, den User um den Inserattext oder das PDF bitten. **Nie Werte aus dem
Gedächtnis ergänzen.**

### 2. Objektprofil extrahieren (listing.json)
Schema: `schemas/listing.schema.json`. Konfliktregeln und Grenzfälle:
`docs/EXTRACTION_ERRORS.md` (massgeblich, auch für die Gold-Dateien des Evals).
- Mit dem Gerüst beginnen: `dealkit extract <datei> --type <TYP> --out listing.json`
  (Dateiname mit Markt-Präfix, z. B. `de-`, `at-`, `bg-`, oder `--market`). Es setzt id, market,
  Red-Flag-Liste (`offen`) und alle Felder auf `fehlend`. Felder füllen, keines löschen.
- Jeder Wert ist ein Evidenz-Objekt `{value, status, source}`.
- `belegt` **nur** mit wörtlichem `quote` aus der Quelle: ein zusammenhängender Ausschnitt,
  in Originalsprache (AL: Albanisch), Zahlen unverändert, ohne «…».
- **Falsche Grösse → `fehlend` + Note; richtige Grösse als Prognose → `geschaetzt`.**
  Preisbereiche, Projektseiten, mehrere oder widersprüchliche Werte → `fehlend`.
- Miete: nur Nettokaltmiete als `monthly_rent`. Warmmiete oder Jahresmiete → `fehlend`,
  Wert und mögliche Umrechnung in `source.note` (nicht selbst umrechnen). «Erzielbare» oder
  «mögliche» Miete → `geschaetzt` mit Note. Bei Kurzzeitvermietung (AL/ME) den Block
  `operating.short_term_rental` füllen und `monthly_rent` auf `fehlend` lassen – das Profil leitet ab.
- Fläche: nur Wohnfläche netto; nur Brutto-/Nutzfläche → `fehlend` + Note.
- Notes auf Deutsch; keine Namen, Telefonnummern oder E-Mails privater Verkäufer übernehmen.
- Quellenstufe ehrlich setzen: Portal/Makler-Angaben sind `portal`/`makler`, nie `amtlich`.
- `market` aus Land/Ort ableiten; `object.type` setzen (steuert die Checkliste).
  AT, MK, BA, BG und HR sind reine Extraktionsmärkte: nach `dealkit validate` enden, kein Screening.
- Preis in der inserierten Währung (`core.currency`: EUR, CHF, BAM, MKD …); Umrechnungen nur in die Note.
- Red Flags stehen im Gerüst (sonst `dealkit checklist <MARKT> --type <TYP>`). Nur Punkte auf
  `geprueft_ok`/`geprueft_risiko` setzen, die der User ausdrücklich bestätigt hat.

### 3. Validieren und screenen
```
dealkit validate listing.json
dealkit screen listing.json -m <mandat> --format md
dealkit screen listing.json -m <mandat> --format json -o assessment.json
```
Lints und Validierungsfehler zuerst beheben (z. B. Jahres- statt Monatsmiete).

### 4. Vorschau zeigen – und hier enden
Die Markdown-Ausgabe unverändert zeigen, darunter maximal drei Sätze Einordnung:
Was bindet den Zielpreis? Welcher offene Blocker ist zuerst zu klären? Was ist nur angenommen?
Dann fragen, ob das Objekt in die Deal-Pipeline (Notion) geschrieben werden soll.

### 5. Optional: in die Deal-Pipeline schreiben
Nur nach Freigabe. Felder: Titel, Markt, Outcome, Score, Zielpreis, Trigger (JSON),
Datenqualität, Link zum Inserat, `assessment.json` als Anhang oder Seiteninhalt.
Bestehenden Eintrag (gleiche `id`) aktualisieren, nicht duplizieren; Preisänderung in
`market_context.price_history` nachführen.

## Wöchentlicher Deal-Lauf (Scheduled Task)
1. Pipeline-Einträge mit Outcome `beobachten` laden.
2. Für jeden: Quelle erneut abrufen; Preis/Verfügbarkeit vergleichen.
3. Trigger prüfen (`price_at_or_below`, `price_drop_pct`, `days_on_market_min`); bei Treffer
   erneut screenen und als «Trigger ausgelöst» in der Vorschau markieren.
4. Nicht mehr verfügbare Objekte auf `verworfen (vom Markt)` setzen und Datum notieren – das ist
   das Ergebnis-Log für die spätere Kalibrierung.
5. Vorschau; keine Statusänderung ohne Freigabe.

## Grenzen
- Keine Aussage zu Marktwert, Miete oder Wertentwicklung ohne Quelle oder Annahme-Kennzeichnung.
- Keine Steuer- oder Rechtsberatung; Hinweise aus dem Marktprofil nur als Prüfpunkte weitergeben.
- Scraping-Blockaden nicht umgehen.
