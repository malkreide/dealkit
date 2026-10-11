#!/usr/bin/env python3
"""Extraction eval for roadmap stage 1.

For every fixture <name>.txt (or .pdf) in the fixture directory, compare the
candidate <name>.pred.json with the hand-made <name>.gold.json:

- core values purchase_price, living_area_m2, monthly_rent within ±1 %
- status exactly equal
- every 'belegt' value in the candidate needs a source.quote that occurs in the
  source text (whitespace-normalised) – the hard gate

Exit codes: 0 ok · 1 hard gate violated (or --min-rate missed) · 2 nothing to
evaluate or a broken gold file. Error classes: docs/EXTRACTION_ERRORS.md.

Usage:
    python scripts/eval_extraction.py [fixtures/listings] [--min-rate 0.9] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dealkit.extraction import evaluate_dir, format_report

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "listings"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extraktions-Eval: *.pred.json gegen *.gold.json und Quelltext prüfen.")
    parser.add_argument("directory", nargs="?", default=str(DEFAULT_DIR), help="Fixture-Verzeichnis (Standard: fixtures/listings)")
    parser.add_argument("--min-rate", type=float, default=None, help="Mindestquote korrekter Fixtures, z. B. 0.9 (Gate Stufe 1)")
    parser.add_argument("--json", action="store_true", help="Bericht als JSON ausgeben")
    args = parser.parse_args(argv)

    report = evaluate_dir(args.directory)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(format_report(report, args.min_rate))
    return report.exit_code(args.min_rate)


if __name__ == "__main__":
    sys.exit(main())
