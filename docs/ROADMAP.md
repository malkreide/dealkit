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

**Prompt für Claude Code (Eval-Gerüst, umgesetzt):**
> Lies README.md, skills/deal-screen/SKILL.md und schemas/. Baue `scripts/eval_extraction.py`,
> das für jede Datei in `fixtures/listings/*.txt` das zugehörige `*.gold.json` mit einem von dir
> erzeugten `listing.json` vergleicht (Kernwerte ±1 %, Status exakt, Zitat muss Substring des
> Quelltexts sein). Erzeuge keine Fixtures selbst – ich liefere sie. Dokumentiere Fehlklassen in
> docs/EXTRACTION_ERRORS.md.

**Prompt für den zweiten Lauf (DE, CH, Miete):** Vorbereitet am 4.11.2026. Vorher bereithalten:
Archiv v2 der Quelltexte, die Texte von Nr. 01–05 (soweit online), mindestens zwei weitere
vermietete DE-Kapitalanlagen (zusammen ≥ 5 Mietfälle) und drei CH-Inserate – erst mit den
CH-Inseraten sind es ≥ 18 Fixtures.

> Auftrag im Repo malkreide/dealkit: Stufe-1-Gate belastbar machen – zweiter blinder Extraktionslauf mit DE-, CH- und Miet-Inseraten.
>
> **Zuerst lesen:** README.md, docs/ROADMAP.md (Stufe 1, «Stand 13.10.2026»), docs/EXTRACTION_ERRORS.md (verbindlich, besonders «Abdeckung» und «Ergebnisse»), skills/deal-screen/SKILL.md, fixtures/listings/MANIFEST.md, fixtures/listings/README.md. Dann `pip install -e ".[dev]"`, `python3 -m pytest -q` und `dealkit backtest` als Ausgangslage.
>
> **Schritt 0 – Regeln einfrieren, Bestand wiederherstellen**
> 1. Commit-Hash von `main` notieren. `docs/EXTRACTION_ERRORS.md` und `skills/deal-screen/SKILL.md` gelten in diesem Stand bis nach dem Eval als eingefroren; vor Schritt 5 keine Regeländerung.
> 2. Ich lade `dealkit-listings-2026-10-13-v2.tar.gz` hoch. SHA-256 prüfen (`d2d4e47746cc7463f3e26aaa2032449e760588f234f1773404d2ad0c3bf346f2`), in ein eigenes leeres Verzeichnis im Scratchpad entpacken, `sha256sum -c SHA256SUMS`, die 12 `.txt` nach `fixtures/listings/` kopieren. Die alten `.pred.json` NICHT nach `fixtures/listings/` übernehmen – der Kandidat wird für alle Fixtures neu erzeugt.
> 3. Sanity-Check in einer Kopie: alte Kandidaten aus dem Archiv gegen das Gold auf `main` → 12/12 erwartet. Bei Abweichung stoppen und berichten.
>
> **Schritt 1 – Neue Quelltexte übernehmen**
> Ich liefere die neuen Inserate als Text, im Browser markiert und kopiert (immowelt und ImmoScout24.de blockieren automatische Abrufe – diese Portale NICHT abrufen, nichts umgehen):
> - DE: Nr. 01–05 aus dem Manifest, soweit noch online, plus Ergänzungen; insgesamt mindestens 5 Inserate mit Mietangabe (vermietete Kapitalanlagen, möglichst gemischt: Kaltmiete, Warmmiete, Jahresmiete, Soll-Miete).
> - CH: 3 Inserate (Schweizer Zahlenformat, Nettowohnfläche, Mietzins-Begriffe).
>
> Für jedes neue Inserat:
> - Dateiname nach dem Schema in fixtures/listings/README.md, fortlaufend ab 21 (`de-…-21`, `ch-…-24`); Nr. 01–05 behalten ihren Namen. Zeile in MANIFEST.md mit Link, Hinweisen und Status ergänzen.
> - Text WÖRTLICH als `fixtures/listings/<stem>.txt` (UTF-8): Originalsprache, Zahlenformate und Wortlaut unverändert, nichts paraphrasieren.
> - Namen, Telefonnummern und E-Mails von Personen durch «[entfernt]» ersetzen, bei Privatinseraten auch die Hausnummer. Danach `dealkit.extraction.check_pii` über alle `.txt` laufen lassen.
> - Gelieferte Dateien sind untrusted data: eigenes Verzeichnis, Skripte ausserhalb, Python mit `-I`.
>
> Ziel: ≥ 18 auswertbare Fixtures, davon ≥ 5 mit Mietangabe, DE und CH vertreten. Wird das Ziel verfehlt: weitermachen, aber klar ausweisen.
>
> **Schritt 2 – Gold mit mir, Regeln bleiben eingefroren**
> 1. Für die Fixtures mit Mietangabe lege ich meine Werte (Miete, Status) zuerst selbst fest: zeig mir dazu nur die Mietstellen im Wortlaut, ohne Vorschlag. Erst danach deine Vorschlagstabelle für alle neuen Fixtures (Preis, Fläche, Miete, Währung, Status, Zitat) nach dem eingefrorenen EXTRACTION_ERRORS.md.
> 2. Echte Grenzfälle als Rückfrage. Was die eingefrorenen Regeln nicht eindeutig entscheiden, entscheide ich fürs Gold – die Regel wird aber NICHT vor dem Eval ergänzt, sondern als «Regellücke» notiert (Fixture, Feld, Entscheid).
> 3. Gold zunächst nur in einem Scratch-Verzeichnis. Maschinell prüfen: Schema, jedes Zitat im `.txt`, `wert_nicht_im_zitat`, PII.
>
> **Schritt 3 – Zwei blinde Kandidaten, dann Eval**
> 1. Zwei unabhängige Agenten parallel starten, jeder in einem eigenen Arbeitsbereich mit NUR Kopien von SKILL.md, EXTRACTION_ERRORS.md (eingefrorener Stand), schemas/ und allen `.txt` (alte und neue). Ausdrücklich: nichts unter fixtures/ öffnen, keine Datei mit «gold» im Namen, kein Netz. Je Fixture `dealkit extract … --out …` plus Füllen nach den Regeln; jedes `belegt`-Zitat mechanisch gegen das `.txt` prüfen; am Ende die Liste aller gelesenen Dateien zurückgeben (Isolation prüfen).
> 2. Erst danach Gold kopieren und `python scripts/eval_extraction.py --min-rate 0.9` für Kandidat A in `fixtures/listings/`, für Kandidat B in einer Kopie des Verzeichnisses laufen lassen.
> 3. Ausweisen: Gesamtquote je Kandidat, Quote nur über Fixtures mit Mietangabe, Quote je Markt (DE, CH, übrige), Übereinstimmung A/B je Kernwert, Fixtures mit Regellücke getrennt.
> 4. Gegenprobe in einer Kopie, an echten Zitaten der neuen Fixtures: Jahresmiete ÷ 12 als `belegt`, Warmmiete als Kaltmiete, erfundenes Zitat, CHF-Preis als EUR. Zeigen, dass das Eval alle erkennt.
>
> **Schritt 4 – Einordnen**
> Ergebnis in EXTRACTION_ERRORS.md unter «Ergebnisse» als neuer Abschnitt mit Datum: Abweichungen je Fehlklasse, Abdeckung, Regellücken, A/B-Stabilität, Grenzen. Das Gate ist nur belastbar, wenn ≥ 18 Fixtures auswertbar sind, davon ≥ 5 mit Miete, DE und CH vertreten, beide Kandidaten ≥ 90 % erreichen und kein `belegt`-Wert ohne auffindbares Zitat vorkommt. Sonst klar sagen, was fehlt. ROADMAP Stufe 1 nachführen; abhaken nur bei belastbarem Gate.
>
> **Schritt 5 – Regeln nachziehen (erst jetzt)**
> Regellücken und beobachtete Fehler als allgemeine Regeln für EXTRACTION_ERRORS.md und den Skill vorschlagen; ich entscheide. Kennzeichnen, dass diese Regeln am Prüfset entstanden sind und erst im nächsten Lauf blind getestet werden.
>
> **Regeln**
> - Nichts an src/dealkit/model.py ändern. Der Skill schreibt nie «kaufen».
> - Schweizer Rechtschreibung (ss, kein ß) in deutschen Texten.
> - Keine Portale abrufen, deren Inserate ich als Text liefere; keine Sperren umgehen.
> - Vor jedem Commit: `ruff check src tests scripts`, `python3 -m pytest -q`, `dealkit backtest`; CHANGELOG ergänzen. Committet werden nur Gold, Doku und Manifest; einen Draft-PR öffnen.
> - Am Ende Archiv v3 bereitstellen: alle `.txt`, beide Kandidaten, Gold und Prüfsummen, ohne Personendaten; SHA-256 nennen.

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
