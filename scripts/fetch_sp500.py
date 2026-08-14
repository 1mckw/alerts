#!/usr/bin/env python3
"""Fetch S&P 500 constituents from Wikipedia and print Python list tuples."""

from __future__ import annotations

import json
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; alerts-scanner/1.0)"}


def fetch_sp500() -> list[tuple[str, str]]:
    url = (
        "https://en.wikipedia.org/w/api.php?"
        "action=parse&page=List_of_S%26P_500_companies&prop=wikitext&format=json"
    )
    req = urllib.request.Request(url, headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = data["parse"]["wikitext"]["*"]

    rows: list[tuple[str, str]] = []
    for block in text.split("\n|-\n"):
        sym_m = re.search(
            r"\{\{(?:Nyse|Nasdaq|NYSE|NASDAQ)Symbol\|([A-Z0-9.]+)\}\}", block, re.I
        )
        if not sym_m:
            continue
        sym = sym_m.group(1).strip()
        name_m = re.search(r"\|\|\s*\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", block)
        if not name_m:
            continue
        name = name_m.group(1).strip()
        name = name.replace("\\", "\\\\").replace('"', '\\"')
        rows.append((sym, name))

    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for sym, name in rows:
        if sym in seen:
            continue
        seen.add(sym)
        out.append((sym, name))
    return out


def main() -> None:
    rows = fetch_sp500()
    if len(rows) < 400:
        raise SystemExit(f"expected ~500 rows, got {len(rows)}")
    print(f"# S&P 500 constituents (source: Wikipedia, count={len(rows)})")
    print("SP500_STOCKS: list[tuple[str, str]] = [")
    for sym, name in rows:
        print(f'    ("{sym}", "{name}"),')
    print("]")


if __name__ == "__main__":
    main()
