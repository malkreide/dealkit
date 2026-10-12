"""Extraction scaffold and extraction eval (roadmap stage 1).

The scaffold is the empty form the deal-screen skill fills: every critical
field starts as 'fehlend', every red-flag question as 'offen'. No LLM is
involved; the scaffold only guarantees that no field is forgotten.

The eval compares a candidate listing (<name>.pred.json) with a hand-made gold
file (<name>.gold.json) and enforces the hard gate of stage 1: no value with
status 'belegt' unless its quote can be found verbatim in the source text.
Error classes are documented in docs/EXTRACTION_ERRORS.md.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .profiles import ALL_MARKETS, market_currency
from .redflags import checklist
from .schema import SCHEMA_DIR, validate

CORE_FIELDS = ("purchase_price", "living_area_m2", "monthly_rent")
TOLERANCE = 0.01  # ±1 % on core values
MARKET_PREFIX = re.compile(rf"^({'|'.join(m.lower() for m in ALL_MARKETS)})-", re.IGNORECASE)
SCAFFOLD_NOTE = "Gerüst: noch nicht extrahiert"

# Listing source kinds that are not evidence source kinds.
_EVIDENCE_KIND = {"offmarket": "nutzer"}


# --- scaffold ---------------------------------------------------------------


def market_from_filename(path: str | Path) -> str | None:
    """'de-leipzig-01.txt' -> 'DE'; None if the prefix is unknown."""
    m = MARKET_PREFIX.match(Path(path).name)
    return m.group(1).upper() if m else None


def listing_id_from_filename(path: str | Path) -> str:
    stem = Path(path).name.split(".", 1)[0].lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


def _missing(kind: str) -> dict:
    return {"value": None, "status": "fehlend", "source": {"kind": kind, "note": SCAFFOLD_NOTE}}


def _object_evidence_fields() -> list[str]:
    """Evidence fields of listing.object, read from the schema so the scaffold stays in sync."""
    schema = json.loads((SCHEMA_DIR / "listing.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]["object"]["properties"]
    return [k for k, v in props.items() if v.get("$ref") == "evidence.schema.json"]


def scaffold(
    path: str | Path,
    *,
    market: str | None = None,
    object_type: str | None = None,
    source_kind: str = "portal",
    url: str | None = None,
    portal: str | None = None,
    now: datetime | None = None,
) -> dict:
    """Build an empty, schema-valid listing for a source file. Reads no content."""
    market = market or market_from_filename(path)
    if market is None:
        prefixes = "/".join(f"{m.lower()}-" for m in ALL_MARKETS)
        raise ValueError(f"Markt nicht aus Dateiname ableitbar ({Path(path).name}); Präfix {prefixes} oder --market angeben")
    kind = _EVIDENCE_KIND.get(source_kind, source_kind)
    now = now or datetime.now(UTC)
    source = {"kind": source_kind, "documents": [Path(path).name]}
    if portal:
        source["portal"] = portal
    if url:
        source["url"] = url
    obj = {"type": object_type} if object_type else {}
    obj.update({k: _missing(kind) for k in _object_evidence_fields()})
    return {
        "id": listing_id_from_filename(path),
        "market": market,
        "captured_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "address": {"country": market},
        "core": {**{k: _missing(kind) for k in CORE_FIELDS}, "currency": market_currency(market)},
        "object": obj,
        "red_flags": [{"id": c.id, "state": "offen"} for c in checklist(market, object_type)],
    }


# --- text helpers -----------------------------------------------------------

_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """NFKC (PDF ligatures, non-breaking spaces), drop soft hyphens, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text).replace("­", "")
    return _WS.sub(" ", text).strip()


def quote_in_source(quote: str | None, source_text: str) -> bool:
    if not quote or not quote.strip():
        return False
    return normalize(quote) in normalize(source_text)


def read_source_text(path: str | Path) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:  # pragma: no cover - depends on environment
            raise RuntimeError("PDF-Fixtures brauchen pypdf: pip install -e '.[pdf]'") from e
        return "\n".join(page.extract_text() or "" for page in PdfReader(p).pages)
    return p.read_text(encoding="utf-8-sig")


_NUM = re.compile(r"\d{1,3}(?:[   '’.,]\d{3})+(?:[.,]\d{1,2})?(?!\d)|\d+(?:[.,]\d+)?")
_MILLION = re.compile(r"\s*(Mio\b|Million)", re.IGNORECASE)


def _interpret(token: str) -> set[float]:
    """All plausible readings of one number token (DE, CH, EN and AL formats)."""
    t = re.sub(r"[   ]", "", token)
    out = set()
    m = re.fullmatch(r"(.*?)[.,](\d{1,2})", t)
    if m:
        out.add(float(re.sub(r"\D", "", m.group(1)) + "." + m.group(2)))
    else:
        out.add(float(re.sub(r"\D", "", t)))
    if len(re.findall(r"[.,'’]", t)) == 1 and "'" not in t and "’" not in t:
        out.add(float(t.replace(",", ".")))
    return out


def numbers_in(text: str) -> set[float]:
    """Numbers a reader could see in a quote: '175.000' -> 175000, '58,5' -> 58.5, '1,25 Mio.' -> 1250000."""
    found: set[float] = set()
    for m in _NUM.finditer(text):
        parts = [m.group(0), *re.split(r"[   ]", m.group(0))]
        values = set().union(*(_interpret(p) for p in parts if p))
        if _MILLION.match(text, m.end()):
            values |= {v * 1_000_000 for v in values}
        found |= values
    return found


def _is_number(v) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def within_tolerance(pred: float, gold: float, tol: float = TOLERANCE) -> bool:
    if gold == 0:
        return pred == 0
    return abs(pred - gold) <= tol * abs(gold)


# --- comparison -------------------------------------------------------------

GATE, ERROR, WARNING, SETUP = "gate", "fehler", "warnung", "setup"
SEVERITY_ORDER = (GATE, SETUP, ERROR, WARNING)


@dataclass
class Finding:
    fixture: str
    path: str
    klass: str
    severity: str  # gate | setup | fehler | warnung
    detail: str = ""


@dataclass
class FixtureResult:
    name: str
    fields: dict[str, bool] = field(default_factory=dict)
    schema_ok: bool = True
    findings: list[Finding] = field(default_factory=list)

    @property
    def gate_ok(self) -> bool:
        return not any(f.severity == GATE for f in self.findings)

    @property
    def correct(self) -> bool:
        """Valid listing, all core fields right and no unsupported 'belegt' value."""
        return self.schema_ok and self.gate_ok and bool(self.fields) and all(self.fields.values())


def iter_evidence(doc, path: str = ""):
    """Yield (path, node) for every evidence object in a listing."""
    if isinstance(doc, dict):
        if {"value", "status", "source"} <= doc.keys():
            yield path, doc
            return
        for k, v in doc.items():
            yield from iter_evidence(v, f"{path}.{k}" if path else k)
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from iter_evidence(v, f"{path}[{i}]")


def _deviation_class(gold: float, pred: float) -> str:
    if gold and pred:
        ratio = pred / gold
        for factor, name in ((12, "faktor_12"), (1000, "faktor_1000"), (10, "faktor_10")):
            if within_tolerance(ratio, factor) or within_tolerance(1 / ratio, factor):
                return name
    return "wert_abweichung"


def compare_field(name: str, path: str, gold: dict | None, pred: dict | None) -> tuple[bool, list[Finding]]:
    """Compare one core field: status exact, value within ±1 %."""
    if not gold:
        return False, [Finding(name, path, "gold_feld_fehlt", SETUP)]
    if not pred:
        return False, [Finding(name, path, "feld_fehlt", ERROR, "Kandidat hat dieses Feld nicht")]
    gs, ps, gv, pv = gold.get("status"), pred.get("status"), gold.get("value"), pred.get("value")
    if gs == "fehlend":
        if ps == "fehlend":
            return True, []
        return False, [Finding(name, path, "konflikt_uebergangen", ERROR, f"Gold fehlend, Kandidat {ps} {pv!r}")]
    if ps == "fehlend":
        return False, [Finding(name, path, "wert_verpasst", ERROR, f"Gold {gs} {gv!r}, Kandidat fehlend")]
    findings = []
    if ps != gs:
        findings.append(Finding(name, path, "status_abweichung", ERROR, f"Gold {gs}, Kandidat {ps}"))
    if not (_is_number(gv) and _is_number(pv)):
        findings.append(Finding(name, path, "wert_typ", ERROR, f"Gold {gv!r}, Kandidat {pv!r}"))
    elif not within_tolerance(pv, gv):
        findings.append(Finding(name, path, _deviation_class(gv, pv), ERROR, f"Gold {gv:g}, Kandidat {pv:g} ({(pv / gv - 1) * 100:+.1f} %)" if gv else f"Gold {gv:g}, Kandidat {pv:g}"))
    return not findings, findings


def check_quotes(name: str, doc: dict, source_text: str, severity: str = GATE, prefix: str = "") -> list[Finding]:
    """Hard gate: every 'belegt' value needs a quote that occurs in the source text."""
    findings = []
    for path, node in iter_evidence(doc):
        if node.get("status") != "belegt":
            continue
        quote = (node.get("source") or {}).get("quote")
        if not quote or not quote.strip():
            findings.append(Finding(name, path, f"{prefix}zitat_fehlt", severity, "status belegt ohne source.quote"))
        elif not quote_in_source(quote, source_text):
            findings.append(Finding(name, path, f"{prefix}zitat_nicht_gefunden", severity, f"«{quote}»"))
    return findings


def check_value_in_quote(name: str, doc: dict, source_text: str) -> list[Finding]:
    """Warning: a found quote that does not show the extracted number (e.g. annual rent quoted, monthly value set)."""
    findings = []
    for key in CORE_FIELDS:
        node = (doc.get("core") or {}).get(key) or {}
        quote, value = (node.get("source") or {}).get("quote"), node.get("value")
        if node.get("status") != "belegt" or not _is_number(value) or not quote_in_source(quote, source_text):
            continue
        if not any(within_tolerance(n, value) for n in numbers_in(quote)):
            findings.append(Finding(name, f"core.{key}", "wert_nicht_im_zitat", WARNING, f"{value:g} nicht in «{quote}»"))
    return findings


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<![\w.,/])(?:(?:\+|00)\d[\d \-/()]{7,}\d|0\d{2,4}[ /-]?\d[\d \-]{4,}\d)")


def check_pii(name: str, doc, path: str = "") -> list[Finding]:
    """Warning: e-mail addresses or phone numbers in a fixture file (no PII of private sellers)."""
    findings = []
    if isinstance(doc, dict):
        for k, v in doc.items():
            if k != "url":
                findings += check_pii(name, v, f"{path}.{k}" if path else k)
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            findings += check_pii(name, v, f"{path}[{i}]")
    elif isinstance(doc, str) and (_EMAIL.search(doc) or _PHONE.search(doc)):
        findings.append(Finding(name, path, "pii_verdacht", WARNING, "E-Mail oder Telefonnummer – entfernen, falls Privatperson"))
    return findings


def compare(name: str, gold: dict, pred: dict | None, source_text: str) -> FixtureResult:
    """Compare a candidate listing with the gold file for one fixture."""
    res = FixtureResult(name)
    gold_errors = validate(gold, "listing")
    if gold_errors:
        res.findings.append(Finding(name, "gold", "gold_ungueltig", SETUP, "; ".join(gold_errors)))
    res.findings += check_quotes(name, gold, source_text, severity=SETUP, prefix="gold_")
    res.findings += check_pii(name, gold, "gold")

    if pred is None:
        res.fields, res.schema_ok = dict.fromkeys(CORE_FIELDS, False), False
        res.findings.append(Finding(name, "pred", "pred_fehlt", ERROR, f"{name}.pred.json nicht vorhanden"))
        return res

    errors = validate(pred, "listing")
    if errors:
        res.schema_ok = False
        res.findings.append(Finding(name, "pred", "schema_ungueltig", ERROR, "; ".join(errors)))
    for key in CORE_FIELDS:
        ok, fs = compare_field(name, f"core.{key}", (gold.get("core") or {}).get(key), (pred.get("core") or {}).get(key))
        res.fields[key] = ok
        res.findings += fs
    # A price is only right in the right currency (BAM vs. EUR differ by ~1.96, not by a factor the value check sees).
    g_cur, p_cur = (gold.get("core") or {}).get("currency", "EUR"), (pred.get("core") or {}).get("currency", "EUR")
    if g_cur != p_cur:
        res.findings.append(Finding(name, "core.currency", "waehrung_abweichung", ERROR, f"Gold {g_cur}, Kandidat {p_cur}"))
        for key in ("purchase_price", "monthly_rent"):
            if ((gold.get("core") or {}).get(key) or {}).get("status") != "fehlend":
                res.fields[key] = False
    res.findings += check_quotes(name, pred, source_text)
    res.findings += check_value_in_quote(name, pred, source_text)
    res.findings += check_pii(name, pred, "pred")
    return res


# --- directory run ----------------------------------------------------------


@dataclass
class EvalReport:
    directory: str
    results: list[FixtureResult] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)

    @property
    def findings(self) -> list[Finding]:
        return [f for r in self.results for f in r.findings]

    @property
    def gate_violations(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == GATE]

    @property
    def fixture_rate(self) -> float:
        return sum(r.correct for r in self.results) / len(self.results) if self.results else 0.0

    @property
    def field_rate(self) -> float:
        n = sum(len(r.fields) for r in self.results)
        return sum(sum(r.fields.values()) for r in self.results) / n if n else 0.0

    def exit_code(self, min_rate: float | None = None) -> int:
        """1 = hard gate violated (or min_rate missed), 2 = nothing to evaluate or broken gold, 0 = ok."""
        if self.gate_violations:
            return 1
        if not self.results or any(f.severity == SETUP for f in self.findings):
            return 2
        if min_rate is not None and self.fixture_rate < min_rate:
            return 1
        return 0

    def to_dict(self) -> dict:
        return {
            "directory": self.directory,
            "fixtures": [{"name": r.name, "fields": r.fields, "schema_ok": r.schema_ok, "gate_ok": r.gate_ok, "correct": r.correct} for r in self.results],
            "fixture_rate": self.fixture_rate,
            "field_rate": self.field_rate,
            "gate_ok": not self.gate_violations,
            "findings": [asdict(f) for f in self.findings],
            "skipped": [{"name": n, "reason": r} for n, r in self.skipped],
        }


_SUFFIXES = (".gold.json", ".pred.json", ".txt", ".pdf")


def evaluate_dir(directory: str | Path) -> EvalReport:
    """Evaluate every fixture <name>.txt|.pdf + <name>.gold.json (+ <name>.pred.json) in a directory."""
    d = Path(directory)
    stems = sorted({p.name[: -len(s)] for p in d.iterdir() for s in _SUFFIXES if p.name.endswith(s)})
    report = EvalReport(str(d))
    for stem in stems:
        source = next((d / f"{stem}{ext}" for ext in (".txt", ".pdf") if (d / f"{stem}{ext}").exists()), None)
        gold, pred = d / f"{stem}.gold.json", d / f"{stem}.pred.json"
        if source is None:
            report.skipped.append((stem, "kein Quelltext (.txt/.pdf) – Zitate nicht prüfbar"))
            continue
        if not gold.exists():
            report.skipped.append((stem, "kein Gold (.gold.json)"))
            continue
        pred_doc = json.loads(pred.read_text(encoding="utf-8")) if pred.exists() else None
        report.results.append(compare(stem, json.loads(gold.read_text(encoding="utf-8")), pred_doc, read_source_text(source)))
    return report


def _pct(rate: float) -> str:
    return f"{rate * 100:.1f} %"


def format_report(report: EvalReport, min_rate: float | None = None) -> str:
    mark = {True: "✓", False: "✗"}
    width = max([len("Fixture"), *(len(r.name) for r in report.results)])
    lines = [f"Extraktions-Eval – {report.directory} ({len(report.results)} Fixtures)", ""]
    if not report.results:
        lines.append("Keine auswertbaren Fixtures (Quelltext .txt/.pdf + .gold.json) gefunden.")
        lines += [f"  übersprungen {name}: {reason}" for name, reason in report.skipped]
        return "\n".join(lines)
    lines.append(f"{'Fixture':<{width}}  Preis  Fläche  Miete  Schema  Zitate  Ergebnis")
    for r in report.results:
        f = r.fields
        lines.append(
            f"{r.name:<{width}}  {mark[f.get('purchase_price', False)]:<5}  {mark[f.get('living_area_m2', False)]:<6}  "
            f"{mark[f.get('monthly_rent', False)]:<5}  {mark[r.schema_ok]:<6}  {mark[r.gate_ok]:<6}  {mark[r.correct]}"
        )
    n = len(report.results)
    n_fields = sum(len(r.fields) for r in report.results)
    lines += [
        "",
        f"Gesamtquote: {sum(r.correct for r in report.results)}/{n} Fixtures korrekt ({_pct(report.fixture_rate)}) · "
        f"Kernwerte {sum(sum(r.fields.values()) for r in report.results)}/{n_fields} ({_pct(report.field_rate)})",
    ]
    if min_rate is not None:
        lines.append(f"Mindestquote {_pct(min_rate)}: {'erreicht' if report.fixture_rate >= min_rate else 'NICHT erreicht'}")
    gv = report.gate_violations
    lines.append("Hartes Gate (kein «belegt» ohne auffindbares Zitat): " + ("OK" if not gv else f"VERLETZT – {len(gv)} Wert(e)"))

    findings = sorted(report.findings, key=lambda f: (SEVERITY_ORDER.index(f.severity), f.klass, f.fixture, f.path))
    if findings:
        lines += ["", "Fehlklassen"]
        counts: dict[tuple[str, str], int] = {}
        for f in findings:
            counts[(f.severity, f.klass)] = counts.get((f.severity, f.klass), 0) + 1
        for (sev, klass), c in counts.items():
            lines.append(f"  {klass:<24} {c:>3}  [{sev}]")
            lines += [f"      {f.fixture} {f.path}" + (f": {f.detail}" if f.detail else "") for f in findings if f.klass == klass and f.severity == sev]
    if report.skipped:
        lines += ["", "Übersprungen"]
        lines += [f"  {name}: {reason}" for name, reason in report.skipped]
    return "\n".join(lines)
