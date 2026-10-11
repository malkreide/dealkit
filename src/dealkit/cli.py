"""Command-line interface: validate, screen, checklist, extract, backtest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .pipeline import render_markdown, screen
from .redflags import checklist
from .schema import lint_listing, load, validate


@click.group()
@click.version_option(__version__)
def main():
    """dealkit – evidence-based real-estate deal screening with a human gate."""


@main.command("validate")
@click.argument("path", type=click.Path(exists=True))
@click.option("--kind", type=click.Choice(["listing", "mandate"]), default="listing")
def validate_cmd(path, kind):
    """Validate a listing or mandate against its schema and run lints."""
    doc = load(path)
    errors = validate(doc, kind)
    for e in errors:
        click.echo(f"ERROR {e}")
    if kind == "listing":
        for w in lint_listing(doc):
            click.echo(f"WARN  {w}")
    click.echo("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


@main.command("screen")
@click.argument("listing", type=click.Path(exists=True))
@click.option("--mandate", "-m", required=True, type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["md", "json"]), default="md")
@click.option("--out", "-o", type=click.Path(), help="Write result to file instead of stdout")
def screen_cmd(listing, mandate, fmt, out):
    """Screen one listing against a mandate and print the recommendation."""
    doc = screen(load(listing), load(mandate))
    text = json.dumps(doc, indent=2, ensure_ascii=False) if fmt == "json" else render_markdown(doc)
    if out:
        Path(out).write_text(text, encoding="utf-8")
        click.echo(f"written {out}: {doc['outcome']} (score {doc['score']})")
    else:
        click.echo(text)


@main.command("checklist")
@click.argument("market", type=click.Choice(["DE", "CH", "AL", "ME", "RS"]))
@click.option("--type", "obj_type", default=None, help="wohnung | haus | mfh | gewerbe | neubau_projekt")
def checklist_cmd(market, obj_type):
    """Print the red-flag checklist for a market (to paste into a listing)."""
    items = [{"id": c.id, "state": "offen", "question": c.question, "severity_if_risk": c.severity_if_risk} for c in checklist(market, obj_type)]
    click.echo(json.dumps(items, indent=2, ensure_ascii=False))


@main.command("extract")
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "-o", type=click.Path(dir_okay=False), help="Write scaffold to file instead of stdout")
@click.option("--market", type=click.Choice(["DE", "CH", "AL", "ME", "RS"]), default=None, help="Override the market derived from the file-name prefix")
@click.option("--type", "obj_type", type=click.Choice(["wohnung", "haus", "mfh", "gewerbe", "neubau_projekt"]), default=None, help="Object type (filters the checklist)")
@click.option("--source-kind", type=click.Choice(["portal", "makler", "expose", "offmarket", "nutzer"]), default="portal")
@click.option("--url", default=None)
@click.option("--force", is_flag=True, help="Overwrite an existing --out file")
def extract_cmd(source, out, market, obj_type, source_kind, url, force):
    """Create the extraction scaffold for a listing text (no LLM).

    Sets id, market (from the prefix de-/ch-/al-/me-/rs-), captured_at, source and the
    red-flag checklist (all 'offen'); every evidence field starts as 'fehlend'. The
    deal-screen skill fills it in.
    """
    from .extraction import scaffold

    try:
        doc = scaffold(source, market=market, object_type=obj_type, source_kind=source_kind, url=url)
    except ValueError as e:
        raise click.UsageError(str(e)) from e
    errors = validate(doc, "listing")
    if errors:  # would be a bug in the scaffold
        raise click.ClickException("scaffold invalid: " + "; ".join(errors))
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if not out:
        click.echo(text, nl=False)
        return
    if Path(out).exists() and not force:
        raise click.ClickException(f"{out} exists – use --force to overwrite (filled values would be lost)")
    Path(out).write_text(text, encoding="utf-8")
    click.echo(f"written {out}: {doc['id']} ({doc['market']}), {len(doc['red_flags'])} red flags offen, all fields fehlend")


@main.command("backtest")
def backtest_cmd():
    """Reproduce the Kompass worked example (300k / 60 m² / 1'200 EUR)."""
    from .model import Inputs, assess

    r = assess(Inputs(purchase_price=300_000, living_area_m2=60, monthly_rent=1_200))
    rows = [
        ("Gesamtinvestition", r.financing.total_investment, 324_000),
        ("Darlehen", r.financing.loan, 244_000),
        ("Rate", r.financing.monthly_payment, 1_220),
        ("Cashflow", r.operating.cash_flow, -246),
        ("Stress-Cashflow", r.stress_cash_flow, -737),
        ("Zielpreis", r.target_price.target, 254_444),
    ]
    for s in r.scenarios:
        if s.name == "basis":
            rows.append((f"Gewinn {s.horizon_years} J", s.profit, {5: 11_151, 10: 68_739, 15: 126_809}[s.horizon_years]))
    ok = True
    for name, got, want in rows:
        match = abs(got - want) <= 1
        ok &= match
        click.echo(f"{'✓' if match else '✗'} {name:<20} {got:>12,.0f}  (Kompass {want:>10,})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
