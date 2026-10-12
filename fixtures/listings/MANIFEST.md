# Fixture-Manifest (Stufe 1)

Quelle der Auswahl: «Immobilien Kompass – Investment-Shortlist, 20 Objekte», Recherchestand
11.10.2026. Die Shortlist selbst ist **kein** Quelltext; Fixtures entstehen ausschliesslich aus den
Originalinseraten unten. Die Hinweise stammen aus der Shortlist und sind am Original zu prüfen;
Preise und Flächen sind bewusst weggelassen, damit sie das Gold nicht vorprägen.

## Quelltext ablegen

1. Link im Browser öffnen, den Inserattext markieren (Titel, Preisblock, Eckdaten, Beschreibung)
   und als `fixtures/listings/<Datei>.txt` speichern (UTF-8). Exposé-PDFs als `<Datei>.pdf`.
2. Zahlen und Formulierungen **nicht** verändern, Originalsprache beibehalten.
3. Namen, Telefonnummern und E-Mail-Adressen von Privatpersonen löschen.
4. Nicht mehr verfügbare Inserate: Datei weglassen und hier in der Spalte «Status» vermerken.

Für alle 20 gibt es eine Zusammenfassung in eigenen Worten (`fixtures/summaries/`, Regeltest).
Sie ersetzt das Original nicht: das Stufe-1-Gate braucht die Originaltexte hier.

`*.txt`, `*.pdf` und `*.pred.json` sind gitignored; committet wird nur `<Datei>.gold.json`.

| Nr | Datei | Markt | Inserat | Hinweise (aus Shortlist, am Original prüfen) | Status |
|---|---|---|---|---|---|
| 01 | `de-leipzig-gohlis-sued-01` | DE | [www.immowelt.de](https://www.immowelt.de/expose/dcd8ea0b-e2e0-4d4f-b9f4-02ac2f04cf7c) | Bezugsfrei → Miete voraussichtlich `fehlend` (oder «erzielbar» → `geschaetzt`, Klasse 8). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 02 | `de-leipzig-lindenthal-02` | DE | [www.immowelt.at](https://www.immowelt.at/expose/dfd2f578-5683-4193-94d2-80efb5b37fa2) | Link führt auf immowelt**.at** – Zuordnung prüfen. Stellplatzerträge von der Wohnungsmiete trennen. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 03 | `de-dresden-blasewitz-03` | DE | [www.immowelt.de](https://www.immowelt.de/expose/1f288aa0-cc77-45c0-a2d4-fb8e40e850f2) | Jahresmiete inseriert → Klasse 3. Hausgeld ist keine Miete (Klasse 2). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 04 | `de-halle-boellberg-04` | DE | [www.immowelt.de](https://www.immowelt.de/expose/4216a8b5-80c5-4211-add3-e036ec4c9ee2) | Jahreskaltmiete inkl. Stellplatz → Klasse 3, Stellplatzanteil unbekannt. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 05 | `de-magdeburg-altneustadt-05` | DE | [www.immowelt.de](https://www.immowelt.de/expose/e52e3d08-309b-431d-be95-b34fe2647b7f) | Zielmiete setzt Modernisierung voraus → Soll-Miete (Klasse 8). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 06 | `de-magdeburg-buckau-06` | DE | [www.immobilienscout24.de](https://www.immobilienscout24.de/expose/171554362) | Bezugsfrei ab November; Hausgeld ist keine Miete (Klasse 2). | nicht mehr verfügbar (410 Gone, 12.10.); Zusammenfassung in `fixtures/summaries/` |
| 07 | `at-graz-geidorf-07` | AT | [www.willhaben.at](https://www.willhaben.at/iad/immobilien/d/eigentumswohnung/steiermark/graz/ideal-fuer-eigennutzer-anleger-attraktive-2-zimmer-wohnung-mit-balkon-in-geidorf-1286254601/) | Nur Extraktion (kein Profil). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 08 | `at-graz-dietrichsteinplatz-08` | AT | [www.immobilienscout24.at](https://www.immobilienscout24.at/expose/6ab53b5d4721c3e4cede41d5) | Nur Extraktion. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 09 | `at-graz-westen-09` | AT | [www.immobilienscout24.at](https://www.immobilienscout24.at/expose/6a880e704feed8e8f3ec91b0) | Energieangaben laut Shortlist unplausibel (kein Kernwert). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 10 | `at-linz-franckviertel-10` | AT | [www.immobilienscout24.at](https://www.immobilienscout24.at/expose/6a226bb44833c10484f804f7) | Nur Extraktion. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 11 | `at-klagenfurt-zentrum-11` | AT | [www.willhaben.at](https://www.willhaben.at/iad/immobilien/d/eigentumswohnung/kaernten/klagenfurt/moderne-singlewohnung-mit-balkon-im-zentrum-von-klagenfurt-zu-verkaufen-1472516466/) | **Privatinserat** – Name, Telefon, E-Mail beim Speichern entfernen (Klasse 13). | abgelaufen (12.10.); Zusammenfassung in `fixtures/summaries/` |
| 12 | `mk-skopje-kiselavoda-12` | MK | [level.mk](https://level.mk/en/property/apartment-sale-skopje-40m2-7/) | Englische Portalversion; Währung prüfen (EUR/MKD). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 13 | `mk-skopje-aerodrom-13` | MK | [level.mk](https://level.mk/en/property/studio-sale-skopje-28m2-2/) | Möbliert; Währung prüfen. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 14 | `rs-novisad-centar-14` | RS | [mail.solis-nekretnine.com](https://mail.solis-nekretnine.com/stan-novi-sad-centar-one-room-apartment/en/1055933/) | «Grundbuchlich eingetragen» ist Anbieteraussage → Red Flag bleibt `offen` (Klasse 16). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 15 | `rs-petrovaradin-15` | RS | [mail.solis-nekretnine.com](https://mail.solis-nekretnine.com/stan-petrovaradin-centar/en/1051896/) | Neubau im Bau, Fläche mit «ca.», Kaufpreisbestandteile unklar → Klassen 1/4. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 16 | `ba-sarajevo-novigrad-16` | BA | [doma.ba](https://doma.ba/nekretnina/sarajevo-cbd3o9qo-680364-5s1v) | Preis in KM → `currency: BAM`, keine EUR-Umrechnung als `belegt` (Klasse 14). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 17 | `al-tirana-myslymshyri-17` | AL | [desrealestate.al](https://desrealestate.al/sq/property/shitet-apartament-21-ne-myslym-shyr-tirane/) | Albanisch; Preis auffällig tief (Aktualität prüfen); Eigentumszertifikat laut Inserat → Red Flag `offen`. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 18 | `bg-plovdiv-izgrev-18` | BG | [imotekapl.imot.bg](https://imotekapl.imot.bg/obiava-1b178547551467263-prodava-dvustaen-apartament-grad-plovdiv-izgrev) | Kyrillisch (Klasse 15); Fläche brutto/netto prüfen (Klasse 5). | Original fehlt; Zusammenfassung in `fixtures/summaries/` |
| 19 | `bg-plovdiv-kyuchukparizh-19` | BG | [prima_casa.imot.bg](https://prima_casa.imot.bg/obiava-1b178704529860087-prodava-dvustaen-apartament-grad-plovdiv-kyuchuk-parizh) | Neubau mit «Akt 16»; tatsächliche Nutzfläche unklar → Klasse 5. | Preisfeld und Text widersprechen sich (12.10.); Zusammenfassung in `fixtures/summaries/` |
| 20 | `hr-osijek-jug-20` | HR | [www.nekretnine.hr](https://www.nekretnine.hr/oglasi/4044593/) | Kroatisch; Fläche brutto/netto prüfen. | Original fehlt; Zusammenfassung in `fixtures/summaries/` |

Verteilung: DE 6 · AT 5 · MK 2 · RS 2 · BA 1 · AL 1 · BG 2 · HR 1. Profile (Screening) gibt es nur für
DE, RS und AL; die übrigen 11 sind Extraktionsmärkte (siehe `docs/ARCHITECTURE.md`, ADR 10).
Gegenüber dem Roadmap-Mix (DE 12 · AL 5 · CH 3) fehlen CH-Inserate ganz, und nur 2–3 Objekte
nennen eine Miete – siehe `docs/EXTRACTION_ERRORS.md`, Abschnitt «Abdeckung».
