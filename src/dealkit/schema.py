"""JSON-schema validation and lints for listings and mandates."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def _registry() -> Registry:
    registry = Registry()
    for p in SCHEMA_DIR.glob("*.schema.json"):
        doc = json.loads(p.read_text(encoding="utf-8"))
        res = Resource.from_contents(doc)
        registry = registry.with_resource(doc["$id"], res).with_resource(p.name, res)
    return registry


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=_registry())


def load(path: str | Path) -> dict:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def validate(doc: dict, name: str) -> list[str]:
    v = validator(name)
    return [f"{'/'.join(str(x) for x in e.path) or '<root>'}: {e.message}" for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path))]


def lint_listing(listing: dict) -> list[str]:
    """Plausibility lints beyond the schema (Kompass 'Plausibilität' gap)."""
    warnings = []
    core = listing.get("core", {})
    price = (core.get("purchase_price") or {}).get("value")
    area = (core.get("living_area_m2") or {}).get("value")
    rent = (core.get("monthly_rent") or {}).get("value")
    market = listing.get("market")
    if price and area:
        ppm2 = price / area
        lo, hi = {"DE": (500, 12_000), "CH": (3_000, 30_000), "AL": (500, 8_000), "ME": (800, 10_000), "RS": (800, 8_000)}.get(market, (100, 50_000))
        if not lo <= ppm2 <= hi:
            warnings.append(f"Preis/m² {ppm2:,.0f} ausserhalb plausiblem Bereich {lo:,}–{hi:,} für {market}")
    if rent and area:
        rpm2 = rent / area
        if not 3 <= rpm2 <= 60:
            warnings.append(f"Miete/m² {rpm2:.1f} unplausibel (3–60) – Monats- vs. Jahresmiete? Kalt vs. warm?")
    if price and rent:
        gy = 12 * rent / price
        if gy > 0.15:
            warnings.append(f"Bruttorendite {gy:.1%} > 15 % – Miete oder Preis vermutlich falsch extrahiert")
    for key in ("purchase_price", "living_area_m2", "monthly_rent"):
        node = core.get(key) or {}
        if node.get("status") == "belegt" and not (node.get("source") or {}).get("quote"):
            warnings.append(f"core.{key}: status 'belegt' ohne Zitat")
        if node.get("source", {}).get("kind") in ("makler", "portal") and key == "monthly_rent" and node.get("status") == "belegt":
            warnings.append("Miete stammt aus Portal/Makler – Mietvertrag anfordern (rent_plausible)")
    return warnings
