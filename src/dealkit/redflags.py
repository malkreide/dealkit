"""Red-flag catalogue per market.

The engine never *answers* these questions. It lists them, tracks their
state (offen / geprueft_ok / geprueft_risiko / nicht_anwendbar) and lets a
finding with severity 'blocker' or 'hoch' override a good financial score.
This replaces the Kompass behaviour where "geprüft" earned points regardless
of the result.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    id: str
    question: str
    severity_if_risk: str  # info | mittel | hoch | blocker
    applies_to: tuple[str, ...] = ("wohnung", "haus", "mfh", "gewerbe", "neubau_projekt")
    source_hint: str = ""


COMMON: tuple[Check, ...] = (
    Check("rent_plausible", "Ist die angesetzte Miete marktüblich und rechtlich zulässig (Ist-Miete belegt, Vergleichsmieten)?", "hoch", source_hint="Mietvertrag, Mietspiegel/Comps"),
    Check("micro_location", "Mikrolage: Lärm, Verkehr, Infrastruktur, Vergleichsangebote geprüft?", "mittel", source_hint="Lärmkarte, OSM, Besichtigung"),
    Check("condition", "Zustand, Energieausweis, Sanierungsbedarf (Dach, Fenster, Heizung, Leitungen) geprüft?", "hoch", source_hint="Energieausweis, Protokolle, Besichtigung"),
    Check("title", "Eigentumstitel und Grundbuch-/Katasterauszug lückenlos (Lasten, Dienstbarkeiten, Vorkaufsrechte)?", "blocker", source_hint="Grundbuch/Kataster"),
    Check("seller_funds_trail", "Source-of-Funds-Dossier (GwG) für diesen Deal angelegt (Transfer, Vertrag, Mieten, Steuern)?", "mittel", source_hint="Bankbelege, Verträge"),
)

MARKET: dict[str, tuple[Check, ...]] = {
    "DE": (
        Check("weg_minutes", "WEG-Protokolle der letzten 3 Jahre, Wirtschaftsplan, Rücklage, beschlossene/absehbare Sonderumlagen geprüft?", "hoch", ("wohnung",), "Verwalter"),
        Check("hausgeld_split", "Hausgeld in umlagefähig / nicht umlagefähig / Rücklage aufgeteilt (keine Doppelzählung)?", "mittel", ("wohnung",), "Wirtschaftsplan"),
        Check("rent_control", "Mietpreisbremse / Kappungsgrenze am Standort und Zulässigkeit der Zielmiete geprüft?", "hoch", source_hint="Landesverordnung, Mietspiegel"),
        Check("epbd_geg", "Energieklasse und GEG/EPBD-Sanierungspflichten (Heizungstausch, Effizienzklasse) als Capex quantifiziert?", "hoch", source_hint="Energieausweis"),
        Check("transfer_tax_state", "Grunderwerbsteuersatz des Bundeslandes im Modell gesetzt?", "info"),
        Check("new_build", "Bei Neubau: Bauträger-Bonität, MaBV-Zahlungsplan, Fertigstellungstermin, § 7b-Fähigkeit (EH40/QNG) geprüft?", "hoch", ("neubau_projekt",)),
        Check("tax_structure", "Haltestruktur (privat vs. vermögensverwaltende GmbH) und DBA CH/DE mit Steuerberater geklärt?", "mittel"),
    ),
    "CH": (
        Check("affordability", "Tragbarkeit nach Bankregel (kalk. Zins 5 %, 15 % Nebenkosten, Amortisation auf 2/3 in 10 Jahren) bestanden?", "blocker"),
        Check("stwe_reglement", "STWE-Reglement, Erneuerungsfonds, Protokolle und anstehende Sanierungen geprüft?", "hoch", ("wohnung",)),
        Check("rent_law", "Mietzins nach VMWG (Referenzzins, Orts-/Quartierüblichkeit, Anfangsmietzins-Anfechtung) geprüft?", "hoch"),
        Check("tax_zh", "Grundstückgewinnsteuer, Liegenschaftensteuerwert 2026 und Schuldzinsenverlegung berücksichtigt?", "mittel"),
    ),
    "AL": (
        Check("ownership_certificate", "Çertifikata e Pronësisë vorhanden und Eintrag im Kataster (ASHK) mit Verkäufer identisch?", "blocker"),
        Check("legalisation", "Gebäude legalisiert (keine informelle Bebauung), Baubewilligung und Nutzungsbewilligung vorhanden?", "blocker"),
        Check("seismic", "Statik nach Erdbebenstandard (post-2019) belegt?", "hoch"),
        Check("notary_escrow", "Zahlung über Notarkonto; Verkäufer-Gewinnsteuer 15 % vor Umschreibung beglichen?", "hoch"),
        Check("str_permit", "Kurzzeitvermietung erlaubt und registriert; Saisonauslastung belegt (nicht Makleraussage)?", "hoch"),
        Check("fx", "Lokale Kosten in Lek – Währungsrisiko im Modell berücksichtigt?", "info"),
    ),
    "ME": (
        Check("title_me", "Grundbuch (list nepokretnosti) sauber, keine Lasten, Verkäufer eingetragen?", "blocker"),
        Check("permits_me", "Bau- und Nutzungsbewilligung vorhanden (viele Küstenobjekte ohne)?", "blocker"),
        Check("season_me", "Auslastung ausserhalb Mai–September realistisch modelliert?", "hoch"),
        Check("tax_me", "Flat Tax 15 % und progressive Übertragungssteuer 3–6 % im Modell?", "info"),
    ),
    "RS": (
        Check("upotrebna_dozvola", "Nutzungsbewilligung (upotrebna dozvola) vorhanden; Objekt legalisiert?", "blocker"),
        Check("restitution", "Restitutionsansprüche früherer Eigentümer anwaltlich ausgeschlossen?", "blocker"),
        Check("clausula", "clausula intabulandi und Katastereintrag (RGZ) vertraglich gesichert?", "blocker"),
        Check("predugovor", "Vorvertrag (predugovor) und kapara 10 % mit Rücktrittsregeln geprüft?", "mittel"),
        Check("reciprocity", "Erwerbsberechtigung (Reziprozität CH/RS) für diesen Objekttyp bestätigt?", "hoch"),
    ),
}


def checklist(market: str, object_type: str | None = None) -> list[Check]:
    items = list(COMMON) + list(MARKET.get(market, ()))
    if object_type:
        items = [c for c in items if object_type in c.applies_to]
    return items


SEVERITY_RANK = {"info": 0, "mittel": 1, "hoch": 2, "blocker": 3}


def evaluate(listing: dict) -> dict:
    """Merge the catalogue with the listing's recorded red_flags.

    Returns open items, risk findings and the maximum severity found.
    """
    market = listing["market"]
    obj_type = (listing.get("object") or {}).get("type")
    catalogue = {c.id: c for c in checklist(market, obj_type)}
    recorded = {rf["id"]: rf for rf in listing.get("red_flags", [])}

    open_items, risks, ok = [], [], []
    for cid, check in catalogue.items():
        rf = recorded.get(cid)
        state = rf["state"] if rf else "offen"
        if state == "offen":
            open_items.append({"id": cid, "question": check.question, "severity_if_risk": check.severity_if_risk})
        elif state == "geprueft_risiko":
            sev = rf.get("severity") or check.severity_if_risk
            risks.append({"id": cid, "severity": sev, "finding": rf.get("finding", "")})
        elif state == "geprueft_ok":
            ok.append(cid)
    max_sev = max((SEVERITY_RANK[r["severity"]] for r in risks), default=-1)
    return {
        "open": open_items,
        "risks": risks,
        "ok": ok,
        "max_risk_severity": next((k for k, v in SEVERITY_RANK.items() if v == max_sev), None),
        "open_blockers": [o["id"] for o in open_items if o["severity_if_risk"] == "blocker"],
    }
