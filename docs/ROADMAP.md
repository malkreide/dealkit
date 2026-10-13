# Roadmap – dealkit

Fünf Stufen mit Gates. Jede Stufe hat einen vorbereiteten Prompt für eine frische
Claude-Code-Session im Repo. Weiter geht es nur, wenn das Gate erreicht ist – sonst wird die
Stufe nachgebessert oder das Projekt eingefroren (Idea Cockpit: ❄️).

Architekturprinzip in jeder Stufe: **KI extrahiert und erklärt · Finanzmodell rechnet
deterministisch · Regeln entscheiden nachvollziehbar · Mensch entscheidet.**

---

## Stufe 0 – Engine-Port und Schemas ✅ (10.10.2026)

- [x] `evidence`, `listing`, `mandate` als JSON-Schema
- [x] Kompass-Modell (`lib/model.ts`) als Python-Paket mit Backtest (9/9 Werte reproduziert)
- [x] Marktprofile DE (Referenz), CH/AL/ME/RS (Stubs)
- [x] Red-Flag-Katalog, Regelwerk `kompass_v1` + `dealkit_v1`, CLI, Skill, 23 Tests

**Gate erreicht:** `dealkit backtest` grün; Beispiel-Screenings liefern `beobachten` (Leipzig)
und `pruefen` mit offenen Blockern (Vlorë).

---

## Stufe 1 – Extraktion mit Provenienz (2–3 Wochen)

Ziel: Aus URL/PDF/Text entsteht ein valides `listing.json`, ohne dass Werte erfunden werden.

- [ ] 20 reale Inserate (DE: 12, AL: 5, CH: 3) als Fixtures sammeln – nur Text/PDF, keine
      personenbezogenen Daten privater Verkäufer speichern
- [ ] Extraktions-Prompt im Skill härten: Konfliktfälle (Preisbereich, Warm/Kalt, Jahresmiete,
      Projektseiten) → `fehlend` + Note
- [ ] Gold-Standard je Fixture manuell erfassen; Script `scripts/eval_extraction.py` vergleicht
      Kernwerte und Status
- [ ] Notion-DB «Deal Pipeline» anlegen (Felder siehe Skill §5); IDs in `config.yml`

**Gate:** Kernwerte (Preis, Fläche, Miete) in ≥ 90 % der Fixtures korrekt **und** kein
einziger erfundener `belegt`-Wert (Zitat muss im Quelltext vorkommen).

**Stand 13.10.2026:** formal erreicht (12/12 korrekt, kein `belegt` ohne Zitat), aber
**nicht belastbar** – nur 12 von 20 Inseraten abrufbar, davon kein DE, kein CH und keines mit
Miete. Stufe 1 bleibt offen, bis ≥ 18 Fixtures (≥ 5 mit Miete) mit eingefrorenen Regeln
blind bestanden sind (siehe `docs/EXTRACTION_ERRORS.md`, «Ergebnisse»).

**Prompt für Claude Code:**
> Lies README.md, skills/deal-screen/SKILL.md und schemas/. Baue `scripts/eval_extraction.py`,
> das für jede Datei in `fixtures/listings/*.txt` das zugehörige `*.gold.json` mit einem von dir
> erzeugten `listing.json` vergleicht (Kernwerte ±1 %, Status exakt, Zitat muss Substring des
> Quelltexts sein). Erzeuge keine Fixtures selbst – ich liefere sie. Dokumentiere Fehlklassen in
> docs/EXTRACTION_ERRORS.md.

---

## Stufe 2 – Sourcing über Alerts und wöchentlicher Deal-Lauf (4–6 Wochen Messfenster)

Ziel: Objekte kommen ohne Handarbeit in die Pipeline; Beobachten funktioniert.

- [ ] Portal-Suchagenten als E-Mail-Alerts (Gmail-Label `deals/<markt>`), Parser nach dem
      Muster von fragment-triage
- [ ] Scheduled Task «Deal-Lauf» (wöchentlich, endet bei Vorschau) – analog «Synthese-Lauf»
- [ ] Korpus: jedes gesehene Inserat als Zeile in `corpus.sqlite` (Fingerprint = Ort + m² +
      Zimmer + gerundeter Preis), Preisverlauf, erstes/letztes Datum
- [ ] Ergebnis-Log: verworfene/vom Markt genommene Objekte mit Datum

**Gate (Messfenster 4 Läufe):** ≥ 5 Objekte pro Woche automatisch erfasst; ≥ 1 Objekt erreicht
«pruefen»; geschätzte Zeitersparnis gegenüber manueller Suche dokumentiert. Wenn 0 Objekte
«pruefen» erreichen: Mandat zu eng oder Markt passt nicht → zurück zu Stufe 0 (Mandat).

**Prompt für Claude Code:**
> Implementiere `dealkit corpus add <listing.json>` und `dealkit corpus history <id>` auf
> SQLite (Tabelle listings, price_events). Fingerprint-Logik in `src/dealkit/corpus.py` mit
> Tests für Relisting-Erkennung (gleiches Objekt, neuer Preis, neue URL). Kein Scraping.

---

## Stufe 3 – Marktkontext und Kalibrierung

- [ ] Comps aus dem Korpus: Preis/m²- und Miete/m²-Verteilung je Quartier (Median, Quartile)
      → `market_context.comparable_*` mit Status `geschaetzt`, Quelle `modell`
- [ ] DE-Open-Data-MCP (Zensus 2022 Wohnen, BBSR, Mietspiegel-Links, Lärmkartierung) nach
      Portfolio-Muster; CH über swiss-housing-mcp / swisstopo-mcp / lindas-mcp
- [ ] Wechselkurse via swiss-snb-mcp für CHF-Sicht im Mandat
- [ ] Kalibrierung: Score gegen Ergebnis-Log auswerten (welche Scores wurden verkauft, zu
      welchem Abschlag?) → `docs/CALIBRATION.md`

**Gate:** Comps weichen beim DE-Fixture-Set im Median < 15 % vom Mietspiegel ab;
mindestens eine Regel wurde aufgrund des Ergebnis-Logs angepasst.

---

## Stufe 4 – Portfolio- und Deinvest-Modul

Nur sinnvoll, wenn ein Objekt gehalten wird.

- [ ] `holding.schema.json` (Kaufdatum, Kaufpreis, Darlehen, Zinsbindungsende, Mietverlauf)
- [ ] Steuerkalender: Spekulationsfrist DE (10 J), Haltedauer-Rabatt GGSt ZH, Ende Zinsbindung
- [ ] Marktwert: CH über AlpVal, DE über Korpus-Comps; «Verkaufsfenster»-Signal
- [ ] GwG-Dossier: Source-of-Funds-Chronologie je Objekt als Markdown generieren

**Gate:** Für ein reales oder synthetisches Holding ein Verkaufsfenster mit Begründung,
das ein Steuerberater nachvollziehen kann.

---

## Stufe 5 – optional: Always-on-Fetcher auf Raspberry Pi 5

- [ ] Pi 5 (vorhanden, Pironman 5 Max) übernimmt Alert-Parsing, Korpus, Scheduler
- [ ] Reasoning bleibt in der Cloud (Claude); kein lokales LLM für Extraktion
- [ ] Kein Cluster, kein K3s – erst wenn Stufe 2 den Dauerbetrieb rechtfertigt

**Gate:** 30 Tage unbeaufsichtigter Betrieb ohne manuellen Eingriff.

---

## Explizit nicht geplant

- Portal-Scraping unter Umgehung von Blockaden oder ToS
- Automatische Kaufempfehlung oder -ausführung
- Öffentliches Produkt mit Empfehlungslogik (FIDLEG-Risiko); publizierbar ist nur der Kernel
