# Extraktions-Fehlklassen (Stufe 1)

Dieses Dokument legt fest, wie der Skill `deal-screen` mit Konfliktfällen umgeht, und ist
damit die Erfassungsregel für die Gold-Dateien. Das Eval (`scripts/eval_extraction.py`)
vergleicht den Status **exakt** – eine Regel, die Gold und Skill unterschiedlich auslegen,
erscheint als Fehler, auch wenn beide «vernünftig» sind.

> **Stand 13.10.2026:** Grenzfälle Stellplatzmiete, Flächen-Schwelle 5 % und BG-Flächen vom
> Owner entschieden (Regeltest auf `fixtures/summaries/`, 12.10.); gerundetes Datenfeld,
> Flächenbezeichnung ohne Zusatz ausserhalb AL/BG und Sprachfassung des Portals am
> 13.10. auf Originaltexten (`fixtures/listings/`, 12 von 20 Inseraten abrufbar).
> Weiterhin nur *erwartet* sind Preisbereiche (Klasse 1), Projektseiten (4) und alle
> Mietfälle (2, 3, 8, 9): Keines der 12 Originalinserate nennt eine Miete (siehe «Abdeckung»
> und «Ergebnisse»).
> Regeln, die nicht tragen, hier ändern – nicht stillschweigend im Gold.

## Grundregel

| Was steht im Inserat? | Status | Wert | Beispiel |
|---|---|---|---|
| Die gesuchte Grösse, eindeutig, wörtlich | `belegt` | wie im Text | «Nettokaltmiete: 600 EUR» |
| Die gesuchte Grösse, aber als Prognose oder Angabe Dritter | `geschaetzt` | wie im Text | «erzielbare Kaltmiete ca. 650 €» |
| Eine **andere** Grösse (warm statt kalt, Jahr statt Monat, brutto statt netto) | `fehlend` | `null` | «Warmmiete 780 €» |
| Mehrere oder widersprüchliche Werte, Bereich, «auf Anfrage» | `fehlend` | `null` | «ab 189.000 €» |
| Nichts | `fehlend` | `null` | – |

**Falsche Grösse → `fehlend` + Note. Richtige Grösse als Prognose → `geschaetzt`.
Richtige Grösse wörtlich → `belegt`.** Treffen mehrere Regeln zu (z. B. jährliche Zielmiete:
Prognose *und* falsche Grösse), gilt die strengere: `fehlend`. Der Skill rechnet nicht um, auch wenn die
Umrechnung trivial scheint (÷ 12). Grund: Jede Umrechnung enthält eine Annahme (sind die
4.320 € Jahresmiete netto kalt? enthält die Warmmiete Heizung?), und `fehlend` löst Regel 1
aus (`daten_vervollstaendigen`). Damit bestätigt ein Mensch den Wert, bevor er die
Empfehlung trägt. Das ist gewollt: lieber ein blockiertes Screening als ein falsches «pruefen».

**Wohin mit der Note:** in `source.note` des betroffenen Felds, auf Deutsch, mit dem
gefundenen Wert und – falls sinnvoll – der möglichen Umrechnung («Jahresmiete 4.320 € →
360 €/Monat, falls netto kalt»). Das auslösende Textstück darf als `source.quote`
mitgeführt werden; bei `fehlend` wird es nicht gegated, erleichtert aber die Nachkontrolle.

**Zitatregel (hartes Gate):** `quote` ist *ein* zusammenhängender, wörtlich kopierter
Ausschnitt in der Originalsprache. Keine Auslassungspunkte, keine Zusammensetzung aus zwei
Stellen, keine Übersetzung, keine umformatierten Zahlen. Das Eval toleriert nur
Unterschiede im Leerraum (Zeilenumbrüche, geschützte Leerzeichen) sowie Unicode-NFKC
(PDF-Ligaturen, `m²` = `m2`).

**Sprachfassung des Portals:** Quelltext ist die Seite, wie sie abgerufen wurde. Liefert das
Portal eine andere Sprachfassung als die Landessprache (z. B. englische Oberfläche mit
Beschreibung in der Landessprache), werden Labels und Zahlenformat der Oberfläche wörtlich
zitiert («Living area 58 m²», «1,250,000 KM»): nicht in die Landessprache zurückübersetzen,
nicht ins lokale Zahlenformat umschreiben. Das Label der Oberfläche gilt als Bezeichnung
im Sinne von Klasse 5. Die Sprachfassung wird im Manifest vermerkt.

## Fehlklassen

### 1. Preisbereich, «ab»-Preis, Preis auf Anfrage

- **Merkmale:** «ab 189.000 €», «189.000 – 245.000 €», «Preis auf Anfrage», «VB auf
  Anfrage», AL «Çmimi: me marrëveshje» (nach Vereinbarung), CH «Preis auf Anfrage» /
  «Richtpreis».
- **Regel:** `purchase_price` → `fehlend` + Note mit dem Bereich. Ein einzelner Preis mit
  «VB» (Verhandlungsbasis) oder «Richtpreis» ist ein Angebotspreis → `belegt`.
- **Grenzfall:** Kaufpreis plus separat ausgewiesener Stellplatz/Inventar («zzgl.
  TG-Stellplatz 15.000 €») → Preis der Einheit `belegt`, Zusatzkosten in die Note.
  Wird nur ein Gesamtpreis inklusive Stellplatz genannt, gilt dieser. Ebenso eine separat
  ausgewiesene Provision oder Gebühr («zzgl. 3 % Provision», RS «+ 3% posrednička
  naknada»): Preis `belegt`, Provision in die Note.
- **Im Eval sichtbar als:** `konflikt_uebergangen` (Skill hat einen Bereichswert
  übernommen), `wert_abweichung` (Unter- oder Obergrenze statt `fehlend`).

### 2. Warm- statt Kaltmiete

- **Merkmale:** DE «Warmmiete», «Gesamtmiete», «Bruttomiete», «Miete inkl. NK»; CH
  «Mietzins inkl. NK», «Bruttomiete», «Miete inkl. Nebenkosten-Akonto».
  Verwandt: **Hausgeld** (DE), **Nebenkosten STWE** (CH) sowie AT «Monatliche Kosten»,
  «Betriebskosten», «Reparaturrücklage» bei Eigentumswohnungen sind Eigentümerkosten,
  nie Miete.
- **Regel:** Nur Nettokaltmiete (CH: Nettomietzins) geht in `monthly_rent`. Steht nur die
  Warmmiete → `fehlend` + Note «Warmmiete 780 €, NK unbekannt». Stehen beide → Kaltmiete
  `belegt`. Hausgeld gehört in `object.hoa_fee_monthly`.
  «Miete» ohne Angabe kalt/warm gilt als Kaltmiete → `belegt`, Note «kalt/warm nicht
  ausgewiesen» – ausser der Text sagt warm, brutto oder inkl. NK/Heizung (AT: «brutto»
  enthält Betriebskosten und USt → `fehlend`).
- **Stellplatz im Kaufgegenstand:** Gehört ein Stellplatz zum Kaufpreis, zählt seine Miete
  zur `monthly_rent`. `belegt` ist die Summe nur, wenn sie im Text steht («zusammen
  492 EUR»); sonst die Wohnungsmiete `belegt` und die Stellplatzmiete in die Note.
- **Im Eval sichtbar als:** `konflikt_uebergangen` oder – wenn Gold die Kaltmiete hat –
  `wert_abweichung` mit typischerweise +15 bis +40 %.

### 3. Jahresmiete

- **Merkmale:** «Jahresnettokaltmiete», «Mieteinnahmen p. a.», «Ist-Miete jährlich»,
  «Mietertrag pro Jahr» (CH-Renditeobjekte), Kapitalanleger-Exposés mit Rendite-Tabellen.
- **Regel:** `monthly_rent` → `fehlend` + Note mit Jahreswert und Umrechnung (÷ 12). Nicht
  selbst umrechnen, nicht den Jahreswert als Monatswert übernehmen.
- **Im Eval sichtbar als:** `faktor_12` (Jahreswert 1:1 übernommen),
  `konflikt_uebergangen` + Warnung `wert_nicht_im_zitat` (umgerechnet und als `belegt`
  markiert – das Zitat zeigt 4.320, der Wert ist 360). Zusätzlich meldet
  `dealkit validate` «Miete/m² unplausibel».

### 4. Projektseite mit mehreren Einheiten

- **Merkmale:** Neubauprojekte mit Preisliste, «Wohnungen von 45 bis 120 m²»,
  «2,5- bis 4,5-Zimmer», mehrere Grundrisse, Bauträger-Landingpages.
- **Regel:** Alle drei Kernwerte `fehlend`, Note «Projektseite, Einheit nicht bestimmt»,
  `object.type` = `neubau_projekt`. Nur wenn die Eingabe eine konkrete Einheit bezeichnet
  (z. B. «WE 12») und deren Zeile im Text steht, werden deren Werte `belegt` – Zitat ist
  dann die Tabellenzeile, wie sie im Quelltext steht.
- **Abgrenzung:** Eine einzelne Einheit im Bau (eigener Inseratcode, eigener Preis, eigene
  Fläche) ist keine Projektseite: `object.type` = `wohnung`, Werte nach den üblichen Regeln,
  Bauzustand und fehlender Grundbucheintrag in die Note (Owner-Entscheid 13.10.2026).
- **Im Eval sichtbar als:** `konflikt_uebergangen` (irgendeine Einheit übernommen),
  oft zusammen mit `zitat_nicht_gefunden`, weil Tabellenzeilen im PDF-Text anders
  umbrochen sind als im Layout.

### 5. Fläche brutto/netto

- **Merkmale:** DE «Wohnfläche» vs. «Nutzfläche», «Wohn-/Nutzfläche», «inkl. Balkon zu
  100 %», «Gesamtfläche»; CH «Nettowohnfläche» vs. «Bruttogeschossfläche (BGF)»,
  «Wohnfläche inkl. Terrasse»; AL «sipërfaqja neto» vs. «sipërfaqja bruto» (bruto enthält
  oft den Anteil an Treppenhaus und Gemeinschaftsflächen, 10–25 % mehr).
- **Regel:** `living_area_m2` ist die Wohnfläche netto (DE: nach WoFlV, CH:
  Nettowohnfläche, AL: neto). Stehen netto und brutto → netto `belegt`, brutto in die Note.
  Steht nur eine Brutto-, Nutz- oder Gesamtfläche, oder ist bei AL unklar, welche gemeint
  ist → `fehlend` + Note mit dem Wert. «ca. 58,5 m²» ist eine Wohnflächenangabe → `belegt`.
- **Bezeichnung:** Massgeblich ist das Wort im Quelltext. «Wohnfläche» → `belegt`.
  «Fläche» ohne Zusatz gilt als Wohnfläche, auch fremdsprachig («Area», «Floor area»,
  «Površina», «Kvadratura»), ausser in Märkten mit Brutto-Konvention (AL, BG) → `fehlend`
  + Note. Die Brutto-Liste ist bewusst kurz: MK, RS, BA und HR gehören nicht dazu
  (Owner-Entscheid 13.10.2026).
- **Datenfeld vs. Text:** Weichen zwei Flächenangaben um höchstens 5 % voneinander ab
  (Rundung, «ungefähr»), ist das kein Widerspruch: Wert aus dem strukturierten Datenfeld
  `belegt`, der andere in die Note. Das gilt auch, wenn das Datenfeld erkennbar eine
  Rundung des Textwerts ist (Feld «64 m²», Text «63,7 m²» → 64): die Regel bleibt
  deterministisch, der genauere Wert steht in der Note. Über 5 % → Klasse 10.
- **Mehrere Datenfelder:** Zeigt die Seite eine Fläche in der Kopfzeile ohne Label und
  eine im beschrifteten Merkmalsfeld («Wohnfläche …»), gilt das beschriftete Feld.
- **Im Eval sichtbar als:** `wert_abweichung` (+10 bis +25 %), `konflikt_uebergangen`.

### 6. Fremdsprache (AL)

- **Merkmale:** Albanische Inserate (gelegentlich Italienisch oder Englisch).
  Wortschatz: *çmimi* Preis, *sipërfaqja* Fläche, *neto/bruto*, *qira (mujore)* Miete
  (monatlich), *shitet* zu verkaufen, *jepet me qira* zu vermieten, *me marrëveshje* nach
  Vereinbarung, *kati* Stockwerk, *1+1* ein Schlafzimmer plus Wohnraum (nicht «2 Zimmer»),
  *me hipotekë* mit eingetragenem Eigentumstitel.
- **Regel:** Zitat wörtlich auf Albanisch, Übersetzung nur in der Note. Zahlenformate
  wörtlich lassen («85.000 €», «85 000 Euro»). Preise in **Lek** prüfen: «lekë të vjetra»
  (alte Lek) sind ein Zehntel neuer Lek – im Zweifel `fehlend` + Note. «Me hipotekë»
  setzt die Red-Flag `ownership_certificate` **nicht** auf `geprueft_ok`; das ist eine
  Makleraussage, kein Katasterauszug.
- **Im Eval sichtbar als:** `zitat_nicht_gefunden` (übersetztes Zitat, hartes Gate),
  `faktor_10` (alte/neue Lek), `wert_abweichung` bei bruto/neto.

### Weitere erwartete Klassen

| # | Klasse | Merkmal | Regel | Eval-Klasse |
|---|---|---|---|---|
| 7 | Zahlenformat | «175.000» (DE) vs. «175,000» (EN), «1'250'000.–» (CH), «1,25 Mio.» | Wert korrekt lesen, Zitat unverändert | `faktor_1000`, `zitat_nicht_gefunden` bei umformatiertem Zitat |
| 8 | Soll- statt Ist-Miete | «erzielbar», «Marktmiete», «nach Sanierung», «Mietpotenzial» | `geschaetzt` (`source.kind` makler/portal) + Note; bei leerstehendem Objekt ohne solche Angabe `fehlend` | `status_abweichung` |
| 9 | Kurzzeitvermietung (AL/ME) | Tagespreise, «Airbnb-Ertrag», Saisonauslastung | `monthly_rent` `fehlend`; Werte in `operating.short_term_rental` (Makleraussagen → `geschaetzt`) | `konflikt_uebergangen` |
| 10 | Widerspruch im selben Inserat | Titel «75 m²», Text «72 m²»; Preisfeld und Text nennen verschiedene Preise | `fehlend` + Note mit beiden Werten. Fläche: bis 5 % Abweichung kein Widerspruch (Klasse 5). Preis: jede Abweichung ist ein Widerspruch, meist eine unbestätigte Preisänderung; eine ausdrückliche Preissenkung («jetzt 169.000 € statt 179.000 €») ist kein Widerspruch → neuer Preis `belegt`, alter in `market_context.price_history` | `konflikt_uebergangen`, `wert_abweichung` |
| 11 | Zitat nicht wörtlich | paraphrasiert, mit «…» gekürzt, aus zwei Stellen zusammengesetzt | ein zusammenhängender Ausschnitt; im Zweifel länger zitieren | `zitat_nicht_gefunden` (Gate) |
| 12 | PDF-Textschicht | Spaltensatz, Silbentrennung «Woh-nfläche», Tabellen, Scan ohne Text | Für das Eval eine bereinigte `<name>.txt` neben das PDF legen (hat Vorrang); Scans ohne Textschicht sind kein Fixture | `zitat_nicht_gefunden`, `gold_zitat_nicht_gefunden` |
| 13 | Personendaten | Name, Telefon, E-Mail privater Verkäufer im Zitat oder in der Note | weglassen; Zitat so wählen, dass es keine enthält | Warnung `pii_verdacht` |
| 14 | Fremdwährung | BA «142.000 KM», MK «денари»/MKD, Plattform zeigt zusätzlich eine EUR-Umrechnung | Preis in der Währung, in der er inseriert ist, `core.currency` entsprechend (`BAM`, `MKD`). Umrechnungen der Plattform oder eigene nie als `belegt`, höchstens in die Note | `waehrung_abweichung` |
| 15 | Kyrillische Schrift | BG, MK, teils RS (ćirilica) | Zitat in Originalschrift, keine Transliteration; Notes auf Deutsch. BG: «застроена площ» ist brutto (inkl. Anteil Gemeinschaftsflächen), «чиста площ» netto → Klasse 5 | `zitat_nicht_gefunden`, `wert_abweichung` |
| 16 | Anbieteraussage als Prüfbefund | «uknjižen» (RS/BA), «Eigentumszertifikat vorhanden» (AL), «Akt 16» (BG), «grundbuchlich eingetragen» | Fakt fürs Objektprofil höchstens als `note`; zugehörige Red Flag bleibt `offen`, bis ein Dokument vorliegt | (nicht im Eval; Red-Flag-Review) |
| 17 | Portal-Rechner | Kreditrate («Monthly payment … /mo», «Monatliche Rate»), «Preis/m² berechnet von …», Kaufnebenkosten- und Renditerechner des Portals | Errechnete Werte sind keine Angaben zum Objekt: nie als Miete, Kosten oder Kernwert übernehmen, nie als Zitat für einen Kernwert verwenden | `konflikt_uebergangen` |

## Abdeckung

Ein Eval ist nur so gut wie seine Fixtures. Lücken der aktuellen Auswahl (Manifest, Stand 13.10.2026):

- **Miete fehlt ganz.** Die drei DE-Inserate mit Mietangabe (Nr. 3–5) sind vom Portal
  blockiert; keines der 12 auswertbaren Inserate nennt eine Miete. `monthly_rent` steht in
  Gold und Kandidat überall auf `fehlend` und zählt als korrekt – geprüft ist damit nur, dass
  keine Miete erfunden wird (Eigentümerkosten und Portal-Rechner wurden nicht übernommen),
  nicht die fehleranfälligste Extraktion (Klassen 2, 3, 8, 9). Quote **nur über Fixtures mit
  Mietangabe**: 0 von 0 – nicht messbar.
- **Kein DE-Inserat.** Der Referenzmarkt mit vollem Profil ist mit 0 von 6 vertreten
  (immowelt und ImmoScout24.de antworten mit Bot-Schutz). Deutsche Begriffe wurden nur an
  drei AT-Inseraten geprüft.
- **Kein CH-Inserat.** Schweizer Zahlenformate («1'250'000.–»), Nettowohnfläche und
  Mietzins-Begriffe (Klassen 2, 5, 7) sind ungetestet.
- **Zugeschnittene Quelltexte.** Die `.txt` enthalten Titel, Preisblock, Datenfelder und
  Beschreibung; Navigation, Werbung, Rechner und ähnliche Objekte sind entfernt. Im Betrieb
  sieht der Skill die ganze Seite (oder was der User einfügt) – mehr Ablenkung als im Eval.

## Ergebnisse

| Datum | Fixtures | Ergebnis | Einordnung |
|---|---|---|---|
| 12.10.2026 | `fixtures/summaries/` (20, Zusammenfassungen) | 20/20 korrekt, Gate OK, keine Warnung | Regeltest, **nicht** das Stufe-1-Gate (siehe unten) |
| 13.10.2026 | `fixtures/listings/` (12 von 20, Originaltexte) | 12/12 korrekt, Kernwerte 36/36, Gate OK, keine Warnung; Gegenprobe 3/3 erkannt | Gate **formal erreicht, nicht belastbar** (siehe unten) |

### 13.10.2026 – Originaltexte

**Ablauf.** Abruf je URL einmal (Manifest), Quelltext wörtlich zugeschnitten, Gold-Entwurf
nach diesem Dokument, Grenzfälle vom Owner entschieden (gerundetes Datenfeld, Flächenlabel
ohne Zusatz ausserhalb AL/BG, Sprachfassung des Portals). Der Kandidat stammt von einem
separaten Agenten, der nur `SKILL.md`, dieses Dokument, `schemas/` und Kopien der `.txt`
sah (kein Zugriff auf `fixtures/` oder Gold; Liste der gelesenen Dateien geprüft). Erst
danach wurden Gold und Kandidat zusammengeführt:
`python scripts/eval_extraction.py --min-rate 0.9` → Exit 0.

**Abweichungen je Fehlklasse** (Vorkommen im Quelltext · Fehler im Kandidaten):

| Klasse | Vorkommen in den 12 Inseraten | Fehler |
|---|---|---|
| 1 Preis + separat ausgewiesene Provision | 2 (RS «+ 3% posrednička naknada») | 0 |
| 2 Eigentümerkosten ≠ Miete | 2 (AT «Monatliche Kosten», «Betriebskosten») | 0 |
| 5/6/15 Fläche ohne neto/bruto in AL/BG | 3 (AL «Sipërfaqe», BG «Площ», «обща площ») | 0 |
| 5 Datenfeld vs. Text ≤ 5 % | 3 (gerundetes Feld; Kopfzeile vs. «Wohnfläche») | 0 |
| 7 Zahlenformate | alle («91 900 €», «85,000 EUR», «€80.000», «142,000 KM», «49,6 m²») | 0 |
| 10 Preisfeld vs. Text | 1 (BG: Feld 99 000 €, Text 102 900) | 0 |
| 14 Fremdwährung | 1 (BA, KM → `BAM`) | 0 |
| 15 Kyrillisch | 2 (BG, Windows-1251) | 0 |
| 16 Anbieteraussage als Prüfbefund | 4 (Grundbuch, Eigentumszertifikat, Akt 16) | 0 (Red Flags `offen`) |
| 17 Portal-Rechner | 9 (berechneter Preis/m², z. B. «Berechnet von willhaben», «KM/m²») | 0 |
| 2, 3, 8, 9 Miete | **0** | – |

Hartes Gate: 20 `belegt`-Werte, alle Zitate wörtlich gefunden (auch über Zeilenumbrüche,
in kyrillischer Schrift und mit Emojis); keine Warnung `wert_nicht_im_zitat`.
Ausserhalb der Kernwerte wich `object.type` bei `rs-petrovaradin-15` ab (Gold
`neubau_projekt` aus dem Regeltest übernommen, Kandidat `wohnung` mit Verweis auf Klasse 4:
eine Einheit, keine Projektseite). Das Eval vergleicht das Feld nicht. Der Owner hat dem
Kandidaten recht gegeben: Gold auf `wohnung` gesetzt, Abgrenzung in Klasse 4 ergänzt.

**Gegenprobe.** In einer Kopie wurden drei Fehler eingebaut und vollständig erkannt (Exit 1,
Quote 9/12): umgerechnete Jahresmiete als `belegt` (dafür erhielt die Kopie eines `.txt` eine
synthetische Zeile «Jahresnettokaltmiete: 6.480 €») → `konflikt_uebergangen` +
`wert_nicht_im_zitat`; erfundenes Zitat → `zitat_nicht_gefunden` (Gate); KM in EUR
umgerechnet → `waehrung_abweichung` + `wert_abweichung` + `wert_nicht_im_zitat`.

**Wie belastbar sind die 12/12?** Das Gate ist formal erreicht (≥ 90 %, kein `belegt`
ohne Zitat), trägt die Freigabe von Stufe 1 aber **nicht**:

- **12 statt mindestens 18 auswertbare Fixtures.** Ein Fehler mehr oder weniger verschiebt
  die Quote um 8 Prozentpunkte.
- **Keine Miete, kein DE, kein CH** (siehe «Abdeckung»). Die riskantesten Klassen sind
  ungeprüft; 12 der 36 korrekten Kernwerte sind «keine Miete genannt → `fehlend`».
- **Regeln am Prüfset geschärft.** Drei Regeln (gerundetes Datenfeld, fremdsprachige
  Flächenlabels, Portalsprache) entstanden am selben Tag an genau diesen Inseraten. Der Lauf
  zeigt, dass sie eindeutig formuliert sind, nicht, dass sie auf neue Inserate tragen.
- **Eine Modellfamilie.** Zuschnitt der Quelltexte, Gold-Entwurf, Regeltexte und Kandidat
  stammen aus derselben Modellfamilie; der Owner hat drei Grenzfälle entschieden und den
  Vorschlag bestätigt, nicht jedes Feld unabhängig erfasst. Ein Lauf, keine Wiederholung.

**Nächster Schritt für ein belastbares Gate:** die sechs DE-Inserate (oder Ersatz) per
Browser kopieren, vermietete Kapitalanlagen mit Miete und 3 CH-Inserate ergänzen (Ziel
≥ 18, davon ≥ 5 mit Miete), Regeln vor dem Lauf einfrieren und den blinden Lauf auf dem
erweiterten Set wiederholen.

### 12.10.2026 – Regeltest auf Zusammenfassungen

**Wie belastbar sind die 20/20?** Der Kandidat wurde von einem separaten Agenten ohne
Zugriff auf das Gold erzeugt, nur aus Quelltext, Skill und diesem Dokument. Ein
Mutationstest mit drei typischen Fehlern (umgerechnete Jahresmiete, Preisfeld trotz
Widerspruch, EUR-Umrechnung mit erfundenem Zitat) wurde vollständig erkannt (Exit 1).
Trotzdem sagt das Ergebnis wenig über echte Inserate:

- Die Zusammenfassungen sind deutsch und vorstrukturiert («Kaufpreis: … · Wohnfläche: …»);
  Konflikte sind ausformuliert («widersprechen sich»), statt versteckt.
- Die Regeln wurden am selben Tag anhand genau dieser Grenzfälle geschärft; der Test
  bestätigt, dass sie **eindeutig formuliert** sind, nicht, dass sie auf neue Fälle tragen.
- Gold-Entwurf, Regeltexte und Kandidat stammen aus derselben Modellfamilie; nur die vier
  Grenzfälle hat ein Mensch entschieden.

Der Vergleich mit den Originalen (13.10.) bestätigt die Grenze: In zwei der zwölf
vergleichbaren Fälle wich das Gold der Zusammenfassung vom Original ab – Nr. 17 übersetzte
«Sipërfaqe» als «Wohnfläche» (Original: AL ohne neto/bruto → `fehlend`), Nr. 20 kannte nur
den Textwert 31,48 m², nicht das Datenfeld.

## Eval-Klassen (Referenz)

| Klasse | Schwere | Bedeutung |
|---|---|---|
| `zitat_fehlt` | **gate** | `belegt` ohne `source.quote` |
| `zitat_nicht_gefunden` | **gate** | Zitat kommt im Quelltext nicht vor (auch ausserhalb der Kernwerte, z. B. `object.year_built`) |
| `gold_ungueltig`, `gold_zitat_*`, `gold_feld_fehlt` | setup | Gold-Datei fehlerhaft → Exit 2, Gold korrigieren |
| `pred_fehlt` | fehler | Kein Kandidat; zählt als Fehlschlag aller drei Kernwerte |
| `schema_ungueltig` | fehler | Kandidat ist kein valides `listing.json` |
| `feld_fehlt` | fehler | Kernwert im Kandidaten nicht vorhanden |
| `konflikt_uebergangen` | fehler | Gold `fehlend`, Kandidat hat einen Wert |
| `wert_verpasst` | fehler | Gold hat einen Wert, Kandidat `fehlend` |
| `status_abweichung` | fehler | beide haben Werte, Status verschieden |
| `wert_abweichung` | fehler | Abweichung > 1 % |
| `faktor_12`, `faktor_1000`, `faktor_10` | fehler | Abweichung um diesen Faktor (Jahres-/Monatsmiete, Tausendertrennzeichen, alte Lek oder Komma) |
| `wert_typ` | fehler | Wert ist keine Zahl |
| `waehrung_abweichung` | fehler | `core.currency` verschieden; Preis und Miete gelten als falsch |
| `wert_nicht_im_zitat` | warnung | Zitat gefunden, zeigt aber den extrahierten Wert nicht |
| `pii_verdacht` | warnung | E-Mail oder Telefonnummer in Gold oder Kandidat |

Ein Fixture gilt als **korrekt**, wenn alle drei Kernwerte stimmen, der Kandidat
schema-valide ist und kein Gate-Verstoss vorliegt. Warnungen beeinflussen die Quote nicht.

**Grenze des Gates:** Die Substring-Prüfung beweist, dass das Zitat existiert – nicht, dass
der Wert dazu passt. Ein Modell kann ein echtes Zitat mit einem falschen Wert verbinden.
Diese Lücke deckt die Warnung `wert_nicht_im_zitat` ab; sie ist bewusst nicht Teil des
harten Gates, weil Zahlenformate mehrdeutig sind. Häufen sich Treffer, sollte sie es werden.
