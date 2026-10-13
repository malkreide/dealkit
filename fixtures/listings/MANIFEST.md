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

## Abruf 13.10.2026

Je URL genau ein Abruf mit `curl` (Standard-User-Agent, Weiterleitungen folgen, 2,5 s Pause),
ohne Umgehung von Bot-Schutz, Captcha oder Login. Aus dem HTML (ohne JavaScript) wurde der
sichtbare Text gezogen und daraus Titel, Preisblock, Datenfelder und Beschreibung wörtlich in
`<Datei>.txt` übernommen; Navigation, Werbung, Rechner, Kontaktformulare und Listen ähnlicher
Objekte sind weggelassen. Leerraum zwischen Elementen ist vereinheitlicht (eine Zeile je
Element), sonst nichts verändert: Originalsprache, Zahlenformate, Emojis bleiben. Ersetzt durch
«[entfernt]» sind Namen, Lizenznummern, Telefonnummern und E-Mail-Adressen von Personen;
Telefonnummern auch dann, wenn sie einer Agentur gehören könnten (oft Mobilnummern einzelner
Makler). Privatinserate waren keine dabei (Nr. 11 ist abgelaufen). Kein Text stammt
ausschliesslich aus eingebettetem JSON.

Ergebnis: **12 von 20 auswertbar.** 6 sind vom Portal blockiert (immowelt, ImmoScout24.de –
also alle DE-Inserate), 2 abgelaufen. Die rohen HTML-Dateien und die `.txt` liegen nur im
Container der Session; für spätere Läufe als Archiv aufbewahren.

Für alle 20 gibt es eine Zusammenfassung in eigenen Worten (`fixtures/summaries/`, Regeltest).
Sie ersetzt das Original nicht: das Stufe-1-Gate braucht die Originaltexte hier.

`*.txt`, `*.pdf` und `*.pred.json` sind gitignored; committet wird nur `<Datei>.gold.json`.

| Nr | Datei | Markt | Inserat | Hinweise (aus Shortlist, am Original prüfen) | Status |
|---|---|---|---|---|---|
| 01 | `de-leipzig-gohlis-sued-01` | DE | [www.immowelt.de](https://www.immowelt.de/expose/dcd8ea0b-e2e0-4d4f-b9f4-02ac2f04cf7c) | Bezugsfrei → Miete voraussichtlich `fehlend` (oder «erzielbar» → `geschaetzt`, Klasse 8). | **blockiert (Portal)** 13.10.: HTTP 403, «Please enable JS and disable any ad blocker» |
| 02 | `de-leipzig-lindenthal-02` | DE | [www.immowelt.at](https://www.immowelt.at/expose/dfd2f578-5683-4193-94d2-80efb5b37fa2) | Link führt auf immowelt**.at** – Zuordnung prüfen. Stellplatzerträge von der Wohnungsmiete trennen. | **blockiert (Portal)** 13.10.: HTTP 403, «Please enable JS and disable any ad blocker» |
| 03 | `de-dresden-blasewitz-03` | DE | [www.immowelt.de](https://www.immowelt.de/expose/1f288aa0-cc77-45c0-a2d4-fb8e40e850f2) | Jahresmiete inseriert → Klasse 3. Hausgeld ist keine Miete (Klasse 2). | **blockiert (Portal)** 13.10.: HTTP 403, «Please enable JS and disable any ad blocker» |
| 04 | `de-halle-boellberg-04` | DE | [www.immowelt.de](https://www.immowelt.de/expose/4216a8b5-80c5-4211-add3-e036ec4c9ee2) | Jahreskaltmiete inkl. Stellplatz → Klasse 3, Stellplatzanteil unbekannt. | **blockiert (Portal)** 13.10.: HTTP 403, «Please enable JS and disable any ad blocker» |
| 05 | `de-magdeburg-altneustadt-05` | DE | [www.immowelt.de](https://www.immowelt.de/expose/e52e3d08-309b-431d-be95-b34fe2647b7f) | Zielmiete setzt Modernisierung voraus → Soll-Miete (Klasse 8). | **blockiert (Portal)** 13.10.: HTTP 403, «Please enable JS and disable any ad blocker» |
| 06 | `de-magdeburg-buckau-06` | DE | [www.immobilienscout24.de](https://www.immobilienscout24.de/expose/171554362) | Bezugsfrei ab November; Hausgeld ist keine Miete (Klasse 2). | **blockiert (Portal)** 13.10.: HTTP 401, Captcha «Ich bin kein Roboter»; am 12.10. bereits 410 Gone |
| 07 | `at-graz-geidorf-07` | AT | [www.willhaben.at](https://www.willhaben.at/iad/immobilien/d/eigentumswohnung/steiermark/graz/ideal-fuer-eigennutzer-anleger-attraktive-2-zimmer-wohnung-mit-balkon-in-geidorf-1286254601/) | Nur Extraktion (kein Profil). | Original 13.10. ✓ (HTML, sichtbarer Text) |
| 08 | `at-graz-dietrichsteinplatz-08` | AT | [www.immobilienscout24.at](https://www.immobilienscout24.at/expose/6ab53b5d4721c3e4cede41d5) | Nur Extraktion. | **abgelaufen** 13.10.: HTTP 410, «Immobilie nicht gefunden» |
| 09 | `at-graz-westen-09` | AT | [www.immobilienscout24.at](https://www.immobilienscout24.at/expose/6a880e704feed8e8f3ec91b0) | Energieangaben laut Shortlist unplausibel (kein Kernwert). | Original 13.10. ✓ |
| 10 | `at-linz-franckviertel-10` | AT | [www.immobilienscout24.at](https://www.immobilienscout24.at/expose/6a226bb44833c10484f804f7) | Nur Extraktion. | Original 13.10. ✓ |
| 11 | `at-klagenfurt-zentrum-11` | AT | [www.willhaben.at](https://www.willhaben.at/iad/immobilien/d/eigentumswohnung/kaernten/klagenfurt/moderne-singlewohnung-mit-balkon-im-zentrum-von-klagenfurt-zu-verkaufen-1472516466/) | **Privatinserat** – Name, Telefon, E-Mail beim Speichern entfernen (Klasse 13). | **abgelaufen** 13.10.: Weiterleitung auf die Suche (`?fromExpiredAdId=…`) |
| 12 | `mk-skopje-kiselavoda-12` | MK | [level.mk](https://level.mk/en/property/apartment-sale-skopje-40m2-7/) | Englische Portalversion; Währung prüfen (EUR/MKD). | Original 13.10. ✓ – englische Portalfassung (Link), Währung EUR |
| 13 | `mk-skopje-aerodrom-13` | MK | [level.mk](https://level.mk/en/property/studio-sale-skopje-28m2-2/) | Möbliert; Währung prüfen. | Original 13.10. ✓ – englische Portalfassung (Link), Währung EUR |
| 14 | `rs-novisad-centar-14` | RS | [mail.solis-nekretnine.com](https://mail.solis-nekretnine.com/stan-novi-sad-centar-one-room-apartment/en/1055933/) | «Grundbuchlich eingetragen» ist Anbieteraussage → Red Flag bleibt `offen` (Klasse 16). | Original 13.10. ✓ – englische Oberfläche, Beschreibung serbisch; Maklername/-nummern entfernt |
| 15 | `rs-petrovaradin-15` | RS | [mail.solis-nekretnine.com](https://mail.solis-nekretnine.com/stan-petrovaradin-centar/en/1051896/) | Neubau im Bau, Fläche mit «ca.», Kaufpreisbestandteile unklar → Klassen 1/4. | Original 13.10. ✓ – englische Oberfläche, Beschreibung serbisch; Maklername/-nummern entfernt |
| 16 | `ba-sarajevo-novigrad-16` | BA | [doma.ba](https://doma.ba/nekretnina/sarajevo-cbd3o9qo-680364-5s1v) | Preis in KM → `currency: BAM`, keine EUR-Umrechnung als `belegt` (Klasse 14). | Original 13.10. ✓ – Portal leitete auf `/en/` um: englische Oberfläche (Zahlenformat «142,000 KM»), Beschreibung bosnisch; Beschreibung stand in einem nachgeladenen HTML-Block und ist an der angezeigten Stelle («About this property») eingesetzt |
| 17 | `al-tirana-myslymshyri-17` | AL | [desrealestate.al](https://desrealestate.al/sq/property/shitet-apartament-21-ne-myslym-shyr-tirane/) | Albanisch; Preis auffällig tief (Aktualität prüfen); Eigentumszertifikat laut Inserat → Red Flag `offen`. | Original 13.10. ✓ – Telefonnummer im Text entfernt |
| 18 | `bg-plovdiv-izgrev-18` | BG | [imotekapl.imot.bg](https://imotekapl.imot.bg/obiava-1b178547551467263-prodava-dvustaen-apartament-grad-plovdiv-izgrev) | Kyrillisch (Klasse 15); Fläche brutto/netto prüfen (Klasse 5). | Original 13.10. ✓ – Windows-1251 → UTF-8 |
| 19 | `bg-plovdiv-kyuchukparizh-19` | BG | [prima_casa.imot.bg](https://prima_casa.imot.bg/obiava-1b178704529860087-prodava-dvustaen-apartament-grad-plovdiv-kyuchuk-parizh) | Neubau mit «Akt 16»; tatsächliche Nutzfläche unklar → Klasse 5. | Original 13.10. ✓ – Windows-1251 → UTF-8; Preisfeld und Text widersprechen sich weiterhin |
| 20 | `hr-osijek-jug-20` | HR | [www.nekretnine.hr](https://www.nekretnine.hr/oglasi/4044593/) | Kroatisch; Fläche brutto/netto prüfen. | Original 13.10. ✓ – Maklername, Telefon, E-Mail entfernt |

Verteilung: DE 6 · AT 5 · MK 2 · RS 2 · BA 1 · AL 1 · BG 2 · HR 1. Profile (Screening) gibt es nur für
DE, RS und AL; die übrigen 11 sind Extraktionsmärkte (siehe `docs/ARCHITECTURE.md`, ADR 10).
Gegenüber dem Roadmap-Mix (DE 12 · AL 5 · CH 3) fehlen CH-Inserate ganz, und nur 2–3 Objekte
nennen eine Miete – siehe `docs/EXTRACTION_ERRORS.md`, Abschnitt «Abdeckung».

Auswertbar (13.10.): AT 3 · MK 2 · RS 2 · BA 1 · AL 1 · BG 2 · HR 1 = 12, **DE 0**. Die drei
DE-Inserate mit Miete (Nr. 3–5) sind alle blockiert; keines der 12 nennt eine Miete.
