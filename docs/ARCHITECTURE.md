# Architektur

```
Mandat (YAML)        Inserat (URL / PDF / Text / Alert-Mail)
     │                          │
     │                 ┌────────▼────────┐
     │                 │  Extraktion     │  LLM (Skill deal-screen)
     │                 │  mit Provenienz │  → listing.json, jede Angabe {value,status,source}
     │                 └────────┬────────┘
     │                          │ validate + lints  (schema.py)
     │                 ┌────────▼────────┐
     │                 │  Marktkontext   │  Stufe 3: Korpus-Comps, Open Data (MCP-Server)
     │                 └────────┬────────┘
     │                          │
     └──────────┐     ┌─────────▼─────────┐
                └────►│  Marktprofil      │  profiles.py: listing + mandate → model.Inputs
                      └─────────┬─────────┘
                      ┌─────────▼─────────┐
                      │  Finanzmodell     │  model.py: deterministisch, Kompass-Port
                      └─────────┬─────────┘
                      ┌─────────▼─────────┐
                      │  Red-Flag-Review  │  redflags.py: Checkliste je Markt, Mensch antwortet
                      └─────────┬─────────┘
                      ┌─────────▼─────────┐
                      │  Regelwerk        │  rules.py: pruefen / beobachten / verwerfen
                      └─────────┬─────────┘
                      ┌─────────▼─────────┐
                      │  Vorschau         │  Markdown + assessment.json → Freigabe → Notion
                      └───────────────────┘
```

## Entscheidungen (ADR-Kurzform)

| # | Entscheidung | Grund |
|---|---|---|
| 1 | Pipeline statt Agenten-Schwarm | Jeder Schritt ist einzeln testbar; der Kompass-Bauplan zeigt, dass Determinismus im Rechenkern der Wert ist. |
| 2 | Evidenz-Objekt für jede Angabe | «Jede Aussage hat Quelle oder ist Annahme» ist nur durchsetzbar, wenn das Schema es erzwingt. Muster aus journeykit. |
| 3 | Mandat als Datei, nicht als Code | Alles, was der Kompass fest eingebaut hatte (4.5 %, Gewichte, −250), ist Investorensache. Muster aus personakit. |
| 4 | Marktprofile als Plugins | DE (fremdfinanziert, Kaltmiete), AL/ME (Cash, Kurzzeitvermietung) und CH (DCF, 75 %) sind nicht dasselbe Modell. |
| 5 | Red Flags werden gelistet, nicht beantwortet | Kaufentscheidende Risiken stehen nicht in Inseraten. «Geprüft» ohne Befund gibt keine Punkte mehr. |
| 6 | Nie «kaufen» | Human Gate; Score ist nicht kalibriert; Anlageberatungs-Risiko. |
| 7 | Kein Scraping | ToS, JS-Rendering, Blockaden. Alerts + manuelle Eingabe sind robuster und legal. |
| 8 | Pi-Cluster gestrichen, Pi 5 optional als Fetcher | Kleine lokale Modelle extrahieren unzuverlässig; K3s löst kein vorhandenes Problem. |
| 9 | `kompass_v1` bleibt im Code | Rückwärts-Backtest gegen `lib/model.ts` und die Kompass-Entscheidungstabelle. |

## Datenqualität

Der schwächste Status unter den drei Kernwerten wird in jeder Bewertung ausgewiesen:

| Status | Bedeutung | Wirkung |
|---|---|---|
| belegt | Zitat aus Quelle | – |
| geschaetzt | aus Evidenz abgeleitet (Modell/Mensch) | Hinweis |
| angenommen | Default ohne objektbezogene Evidenz | Hinweis in Begründung |
| fehlend | unbekannt | blockiert positive Empfehlung |

Quellenstufen (`source.kind`): `amtlich` > `expose` ≈ `nutzer` > `portal` ≈ `makler` > `modell` > `annahme`.
