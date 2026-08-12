#!/usr/bin/env python3
"""DJI30 (^DJI) AR/DR + trend-line touch scanner on 1D."""

from __future__ import annotations

import html
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

import ardr
import trendlines as tl

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "signals")
STATIC_DIR = os.path.join(ROOT, "static")
CHART_PACKS_PATH = os.path.join(OUT_DIR, "chart-packs.json")

# Yahoo Finance symbol for Dow Jones Industrial Average (DJI30)
SYMBOL = "^DJI"
DISPLAY = "DJI30"
NAME = "道瓊 30"
GROUP = "dji"
TIMEFRAME = "1d"

LOOKBACK = ardr.LOOKBACK
VOL_LEN = ardr.VOL_LEN
DROP_PCT = ardr.DROP_PCT
MIN_STREAK = ardr.MIN_STREAK
VOL_MULT = ardr.VOL_MULT
USE_STRUCTURE = ardr.USE_STRUCTURE
TOUCH_WINDOW_BARS = ardr.TOUCH_WINDOW_BARS
NEAR_MISS_TOL_PCT = ardr.NEAR_MISS_TOL_PCT
FRESH_BARS = ardr.FRESH_BARS
BARS = 2000
CHART_BARS = 800

detect_signals = ardr.detect_signals
collect_late_ar_dr_touches = ardr.collect_late_ar_dr_touches
collect_late_ar_dr_near_misses = ardr.collect_late_ar_dr_near_misses
fresh_range = ardr.fresh_range

PIVOT_HIGH = tl.PIVOT_HIGH
PIVOT_LOW = tl.PIVOT_LOW
TREND_EXCEED_MIN_BARS = tl.TREND_EXCEED_MIN_BARS
TREND_EXCEED_MAX_BARS = tl.TREND_EXCEED_MAX_BARS
TREND_EXCEED_BARS = tl.TREND_EXCEED_BARS
build_auto_trend_lines = tl.build_auto_trend_lines
check_line_invalidation = tl.check_line_invalidation
find_trend_touch = tl.find_trend_touch
find_trend_exceed = tl.find_trend_exceed
line_end_at_break = tl.line_end_at_break

UA = {"User-Agent": "Mozilla/5.0 (compatible; DJI30-Alerts/1.0)"}
KIND_ORDER = {"trend_exceed": 0, "ar_dr_touch": 1, "ar_dr_near": 2, "trend_touch": 3}


def chart_key(group: str, symbol: str, timeframe: str) -> str:
    return f"{group}|{symbol}|{timeframe}"


def http_get_json(url: str, timeout: int = 45) -> Any:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def yahoo_range(bars: int) -> str:
    if bars <= 500:
        return "2y"
    if bars <= 2000:
        return "5y"
    if bars <= 3000:
        return "10y"
    return "max"


def fetch_yahoo(symbol: str, bars: int = BARS) -> list[dict]:
    yrange = yahoo_range(bars)
    hosts = [
        "https://query1.finance.yahoo.com",
        "https://query2.finance.yahoo.com",
    ]
    last_err: Exception | None = None
    for host in hosts:
        url = (
            f"{host}/v8/finance/chart/"
            + urllib.parse.quote(symbol, safe="=-.^")
            + f"?interval=1d&range={yrange}&includePrePost=false"
        )
        try:
            payload = http_get_json(url)
            result = (payload.get("chart") or {}).get("result") or []
            if not result:
                continue
            r0 = result[0]
            ts = r0.get("timestamp") or []
            q0 = ((r0.get("indicators") or {}).get("quote") or [{}])[0]
            out = []
            for i, t in enumerate(ts):
                o, h, l, c = (
                    (q0.get("open") or [None])[i],
                    (q0.get("high") or [None])[i],
                    (q0.get("low") or [None])[i],
                    (q0.get("close") or [None])[i],
                )
                v = (q0.get("volume") or [0])[i] or 0
                if None in (o, h, l, c):
                    continue
                out.append(
                    {
                        "time": int(t),
                        "open": float(o),
                        "high": float(h),
                        "low": float(l),
                        "close": float(c),
                        "volume": float(v),
                    }
                )
            if out:
                return out[-bars:] if len(out) > bars else out
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    if last_err:
        raise last_err
    return []


def collect_trend_touches(candles: list[dict], lines: list[dict]) -> list[dict]:
    if not candles:
        return []
    lo, last = fresh_range(len(candles))
    hits = []
    for line in lines:
        if check_line_invalidation(candles, line):
            continue
        touch = find_trend_touch(candles, line)
        if not touch or not (lo <= touch["index"] <= last):
            continue
        label = "阻力趨勢線觸碰" if line["type"] == "resistance" else "支撐趨勢線觸碰"
        hits.append(
            {
                "kind": "trend_touch",
                "label": label,
                "type": line["type"],
                "time": touch["time"],
                "index": touch["index"],
                "level": touch["price"],
                "close": touch["close"],
            }
        )
    return hits


def collect_trend_exceeds(candles: list[dict], lines: list[dict]) -> list[dict]:
    hits = []
    for line in lines:
        exc = find_trend_exceed(candles, line)
        if not exc:
            continue
        label = "阻力趨勢線超出" if line["type"] == "resistance" else "支撐趨勢線超出"
        hits.append(
            {
                "kind": "trend_exceed",
                "label": label,
                "type": line["type"],
                "time": exc["time"],
                "index": exc["index"],
                "level": exc["price"],
                "close": exc["close"],
                "exceed_bars": exc["bars"],
            }
        )
    return hits


def build_chart_pack(candles: list[dict], signals: list[dict], lines: list[dict]) -> dict:
    last_time = int(candles[-1]["time"]) if candles else 0
    rays = [ardr.signal_to_chart_ray(sig, candles, last_time) for sig in signals]
    trend = []
    for line in lines:
        invalidated = check_line_invalidation(candles, line)
        end_time, end_price = line_end_at_break(candles, line)
        trend.append(
            {
                "type": line["type"],
                "p1": {"time": int(line["p1"]["time"]), "price": float(line["p1"]["price"])},
                "p2": {"time": int(line["p2"]["time"]), "price": float(line["p2"]["price"])},
                "endTime": int(end_time),
                "endPrice": float(end_price),
                "invalidated": invalidated,
            }
        )
    trimmed = candles[-CHART_BARS:] if len(candles) > CHART_BARS else candles
    return {
        "candles": [
            {
                "time": int(c["time"]),
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
            }
            for c in trimmed
        ],
        "rays": rays,
        "trend_lines": trend,
    }


def scan_one() -> dict:
    candles = fetch_yahoo(SYMBOL)
    signals = detect_signals(candles)
    late = collect_late_ar_dr_touches(candles, signals)
    near = collect_late_ar_dr_near_misses(candles, signals)
    lines = build_auto_trend_lines(candles)
    trend = collect_trend_touches(candles, lines)
    exceed = collect_trend_exceeds(candles, lines)
    events = late + near + trend + exceed
    for ev in events:
        ev["timeframe"] = TIMEFRAME
    return {
        "group": GROUP,
        "symbol": DISPLAY,
        "yahoo_symbol": SYMBOL,
        "name": NAME,
        "source": "yahoo",
        "timeframe": TIMEFRAME,
        "bars": len(candles),
        "events": events,
        "error": None,
        "chart": build_chart_pack(candles, signals, lines),
    }


def fmt_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def fmt_num(v: float) -> str:
    return f"{v:.6g}"


def read_static(name: str) -> str:
    with open(os.path.join(STATIC_DIR, name), encoding="utf-8") as f:
        return f.read()


def render_html(payload: dict) -> str:
    hits = payload["hits"]
    ar_dr = [h for h in hits if h["kind"] == "ar_dr_touch"]
    ar_near = [h for h in hits if h["kind"] == "ar_dr_near"]
    trend = [h for h in hits if h["kind"] == "trend_touch"]
    exceed = [h for h in hits if h["kind"] == "trend_exceed"]
    c = payload["counts"]
    charts = payload.get("charts") or {}
    ck = chart_key(GROUP, DISPLAY, TIMEFRAME)
    chart_pack = charts.get(ck, {})

    def sym_btn(h: dict) -> str:
        attrs = (
            f'data-symbol="{html.escape(DISPLAY, quote=True)}" '
            f'data-group="{html.escape(GROUP, quote=True)}" '
            f'data-name="{html.escape(NAME, quote=True)}" '
            f'data-tf="1d" data-level="{html.escape(str(h.get("level", "")), quote=True)}" '
            f'data-type="{html.escape(str(h.get("type", "")), quote=True)}" '
            f'data-kind="{html.escape(str(h.get("kind", "")), quote=True)}" '
            f'data-time="{html.escape(str(h.get("time", "")), quote=True)}"'
        )
        return (
            f'<button type="button" class="sym-btn" {attrs} title="開啟蠟燭圖">'
            f"<code>{html.escape(DISPLAY)}</code></button>"
        )

    def rows(items: list[dict], empty: str, cols: int, builder) -> str:
        if not items:
            return f'<tr><td colspan="{cols}" class="empty">{empty}</td></tr>'
        return "\n".join(builder(h) for h in items)

    def row_ar_dr(h: dict) -> str:
        cls = "ar" if h.get("type") == "AR" else "dr"
        return (
            f"<tr>"
            f'<td><span class="tag {cls}">{html.escape(str(h.get("type", "")))}</span></td>'
            f"<td>{sym_btn(h)}</td>"
            f"<td>{html.escape(h.get('name', NAME))}</td>"
            f'<td class="num">{fmt_num(float(h["level"]))}</td>'
            f'<td class="num">{int(h.get("bars_after_signal", 0))}</td>'
            f"<td>{html.escape(fmt_ts(int(h['time'])))}</td>"
            "</tr>"
        )

    def row_ar_near(h: dict) -> str:
        cls = "ar" if h.get("type") == "AR" else "dr"
        return (
            f"<tr>"
            f'<td><span class="tag {cls}">{html.escape(str(h.get("type", "")))}</span></td>'
            f"<td>{sym_btn(h)}</td>"
            f"<td>{html.escape(h.get('name', NAME))}</td>"
            f'<td class="num">{fmt_num(float(h["level"]))}</td>'
            f'<td class="num">{float(h.get("gap_pct", 0)):.3g}%</td>'
            f'<td class="num">{int(h.get("bars_after_signal", 0))}</td>'
            f"<td>{html.escape(fmt_ts(int(h['time'])))}</td>"
            "</tr>"
        )

    def row_trend(h: dict) -> str:
        cls = "resist" if h.get("type") == "resistance" else "support"
        return (
            f"<tr>"
            f'<td><span class="tag {cls}">{html.escape(str(h.get("type", "")))}</span></td>'
            f"<td>{sym_btn(h)}</td>"
            f"<td>{html.escape(h.get('name', NAME))}</td>"
            f'<td class="num">{fmt_num(float(h["level"]))}</td>'
            f"<td>{html.escape(fmt_ts(int(h['time'])))}</td>"
            "</tr>"
        )

    def row_exceed(h: dict) -> str:
        cls = "resist" if h.get("type") == "resistance" else "support"
        return (
            f"<tr>"
            f'<td><span class="tag {cls}">{html.escape(str(h.get("type", "")))}</span></td>'
            f"<td>{sym_btn(h)}</td>"
            f"<td>{html.escape(h.get('name', NAME))}</td>"
            f'<td class="num">{fmt_num(float(h["level"]))}</td>'
            f'<td class="num">{int(h.get("exceed_bars", TREND_EXCEED_BARS))}</td>'
            f"<td>{html.escape(fmt_ts(int(h['time'])))}</td>"
            "</tr>"
        )

    gen = html.escape(payload["generated_at"])
    embed_js = (
        "<script>window.CHART_PACKS = "
        + json.dumps({ck: chart_pack}, ensure_ascii=False, separators=(",", ":"))
        + ";window.SYMBOL_CATALOG = "
        + json.dumps(
            [
                {
                    "group": GROUP,
                    "symbol": DISPLAY,
                    "name": NAME,
                    "timeframe": TIMEFRAME,
                    "hasHit": bool(hits),
                    "hasChart": bool(chart_pack.get("candles")),
                }
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + ";window.WATCHLISTS = {};</script>\n"
    )

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="3600" />
  <title>DJI30 Touch Alerts</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg: #000; --panel: rgba(8,12,20,.58); --border: rgba(0,255,213,.18);
      --text: #eefdfb; --muted: #7a93a8; --primary: #00f0c8;
      --ar: #00e896; --dr: #ff4d6d;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Space Grotesk", system-ui, sans-serif;
      background: #000; color: var(--text); min-height: 100vh; padding: 28px 18px 48px;
    }}
    .wrap {{ max-width: 960px; margin: 0 auto; }}
    h1 {{ font-size: 1.5rem; color: var(--primary); }}
    .meta {{ color: var(--muted); font-size: .9rem; margin: 8px 0 18px; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 22px; }}
    @media (max-width: 720px) {{ .cards {{ grid-template-columns: 1fr 1fr; }} }}
    .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; }}
    .card .lbl {{ font-size: .65rem; color: var(--muted); text-transform: uppercase; }}
    .card .val {{ font-family: "JetBrains Mono", monospace; font-size: 1.2rem; font-weight: 700; margin-top: 4px; }}
    h2 {{ font-size: 1.05rem; margin: 22px 0 10px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .84rem; }}
    th, td {{ padding: 9px 12px; text-align: left; border-bottom: 1px solid rgba(0,240,200,.08); }}
    th {{ color: var(--muted); font-size: .68rem; text-transform: uppercase; }}
    td.num, th.num {{ text-align: right; font-family: "JetBrains Mono", monospace; }}
    td.empty {{ text-align: center; color: var(--muted); padding: 22px; }}
    code {{ font-family: "JetBrains Mono", monospace; color: var(--primary); }}
    .tag {{ display: inline-block; font-size: .72rem; padding: 2px 7px; border-radius: 5px; font-weight: 700; }}
    .tag.ar {{ background: rgba(0,232,150,.14); color: var(--ar); }}
    .tag.dr {{ background: rgba(255,77,109,.14); color: var(--dr); }}
    .tag.resist {{ background: rgba(255,77,109,.14); color: var(--dr); }}
    .tag.support {{ background: rgba(0,232,150,.14); color: var(--ar); }}
    .sym-btn {{ background: none; border: 0; padding: 0; cursor: pointer; color: inherit; }}
    .sym-btn:hover code {{ text-decoration: underline; }}
    footer {{ margin-top: 28px; color: var(--muted); font-size: .75rem; }}
    a {{ color: var(--primary); }}
    .chart-cta {{
      display: inline-flex; align-items: center; gap: 8px; margin: 12px 0 20px;
      padding: 10px 16px; border-radius: 10px; border: 1px solid var(--border);
      background: rgba(0,240,200,.06); color: var(--primary); cursor: pointer; font: inherit;
    }}
    .modal {{
      position: fixed; inset: 0; z-index: 80; display: flex; align-items: center; justify-content: center;
      padding: 16px; background: rgba(0,0,0,.62); opacity: 0; pointer-events: none; transition: opacity .2s;
    }}
    .modal.open {{ opacity: 1; pointer-events: auto; }}
    .modal-panel {{
      width: min(1100px, 100%); height: min(720px, 92vh);
      background: rgba(8,12,20,.9); border: 1px solid var(--border); border-radius: 16px;
      display: flex; flex-direction: column; overflow: hidden;
    }}
    .modal-head {{ display: flex; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--border); }}
    .modal-close {{ width: 40px; height: 40px; border-radius: 10px; border: 1px solid var(--border); background: transparent; color: var(--text); cursor: pointer; }}
    .modal-chart {{ flex: 1; min-height: 0; position: relative; background: #000; }}
    .modal-chart #lwc {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
    .modal-status {{ position: absolute; inset: 0; display: grid; place-items: center; color: var(--muted); }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>DJI30 · AR/DR &amp; 趨勢線 Alerts</h1>
    <p class="meta">商品 <strong>{html.escape(DISPLAY)}</strong>（Yahoo <code>{html.escape(SYMBOL)}</code>）· 週期 <strong>1D</strong> · 更新 {gen}</p>
    <div class="cards">
      <div class="card"><div class="lbl">AR/DR 觸碰</div><div class="val">{c['ar_dr_touch']}</div></div>
      <div class="card"><div class="lbl">AR/DR 接近</div><div class="val">{c['ar_dr_near']}</div></div>
      <div class="card"><div class="lbl">趨勢線觸碰</div><div class="val">{c['trend_touch']}</div></div>
      <div class="card"><div class="lbl">趨勢線超出</div><div class="val">{c['trend_exceed']}</div></div>
    </div>
    <button type="button" class="chart-cta sym-btn"
      data-symbol="{html.escape(DISPLAY, quote=True)}"
      data-group="{html.escape(GROUP, quote=True)}"
      data-name="{html.escape(NAME, quote=True)}"
      data-tf="1d" data-kind="manual" data-type="" data-level="">
      開啟 DJI30 圖表（AR/DR 射線 + 趨勢線）
    </button>

    <h2>趨勢線超出（最新 {TREND_EXCEED_MIN_BARS}–{TREND_EXCEED_MAX_BARS} 根）</h2>
    <div class="panel"><table><thead><tr>
      <th>類型</th><th>代碼</th><th>名稱</th><th class="num">價位</th><th class="num">根數</th><th>時間</th>
    </tr></thead><tbody>{rows(exceed, "目前無超出信號", 6, row_exceed)}</tbody></table></div>

    <h2>AR / DR 觸碰（&gt;{TOUCH_WINDOW_BARS} 根後）</h2>
    <div class="panel"><table><thead><tr>
      <th>類型</th><th>代碼</th><th>名稱</th><th class="num">價位</th><th class="num">根數</th><th>時間</th>
    </tr></thead><tbody>{rows(ar_dr, "目前無 AR/DR 觸碰", 6, row_ar_dr)}</tbody></table></div>

    <h2>AR / DR 接近未觸</h2>
    <div class="panel"><table><thead><tr>
      <th>類型</th><th>代碼</th><th>名稱</th><th class="num">價位</th><th class="num">差距</th><th class="num">根數</th><th>時間</th>
    </tr></thead><tbody>{rows(ar_near, f"目前無接近未觸（&gt;{TOUCH_WINDOW_BARS} 根後）", 7, row_ar_near)}</tbody></table></div>

    <h2>趨勢線觸碰</h2>
    <div class="panel"><table><thead><tr>
      <th>類型</th><th>代碼</th><th>名稱</th><th class="num">價位</th><th>時間</th>
    </tr></thead><tbody>{rows(trend, "目前無趨勢線觸碰", 5, row_trend)}</tbody></table></div>

    <footer>
      每小時自動更新 · GitHub Pages ·
      <a href="latest.json">latest.json</a>
    </footer>
  </div>

  <div id="chart-modal" class="modal" hidden aria-hidden="true">
    <div class="modal-panel" role="dialog">
      <div class="modal-head">
        <div>
          <div id="chart-title" class="modal-title">Chart</div>
          <div id="chart-sub" class="modal-sub"></div>
        </div>
        <button type="button" class="modal-close" id="chart-close" aria-label="關閉">×</button>
      </div>
      <div class="modal-chart" id="chart-body">
        <div class="modal-status" id="chart-status">載入中…</div>
        <div id="lwc" hidden></div>
        <iframe id="tv-frame" title="TradingView chart" hidden></iframe>
      </div>
    </div>
  </div>
{embed_js}{read_static("report-chart-modal.html")}
</body>
</html>
"""


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Scanning {DISPLAY} ({SYMBOL}) 1D…", flush=True)
    try:
        result = scan_one()
    except Exception as exc:  # noqa: BLE001
        print(f"Scan failed: {exc}", flush=True)
        result = {
            "group": GROUP,
            "symbol": DISPLAY,
            "yahoo_symbol": SYMBOL,
            "name": NAME,
            "source": "yahoo",
            "timeframe": TIMEFRAME,
            "bars": 0,
            "events": [],
            "error": str(exc),
        }

    hits = []
    charts: dict[str, dict] = {}
    pack = result.pop("chart", None)
    if pack and not result.get("error"):
        key = chart_key(GROUP, DISPLAY, TIMEFRAME)
        charts[key] = pack
    for ev in result.get("events") or []:
        hits.append(
            {
                **ev,
                "group": GROUP,
                "symbol": DISPLAY,
                "name": NAME,
                "timeframe": TIMEFRAME,
            }
        )
    hits.sort(key=lambda x: KIND_ORDER.get(x["kind"], 99))

    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = {
        "generated_at": generated_at,
        "symbol": DISPLAY,
        "yahoo_symbol": SYMBOL,
        "name": NAME,
        "timeframe": TIMEFRAME,
        "params": {
            "bars": BARS,
            "touch_window_bars": TOUCH_WINDOW_BARS,
            "drop_pct": DROP_PCT,
            "min_streak": MIN_STREAK,
            "vol_mult": VOL_MULT,
        },
        "counts": {
            "ar_dr_touch": sum(1 for h in hits if h["kind"] == "ar_dr_touch"),
            "ar_dr_near": sum(1 for h in hits if h["kind"] == "ar_dr_near"),
            "trend_touch": sum(1 for h in hits if h["kind"] == "trend_touch"),
            "trend_exceed": sum(1 for h in hits if h["kind"] == "trend_exceed"),
            "hits": len(hits),
        },
        "hits": hits,
        "results": [result],
        "charts": charts,
        "error": result.get("error"),
    }

    with open(os.path.join(OUT_DIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    chart_payload = {
        "generated_at": generated_at,
        "group": GROUP,
        "symbol": DISPLAY,
        "charts": charts,
    }
    with open(CHART_PACKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chart_payload, f, ensure_ascii=False, separators=(",", ":"))

    page = render_html(payload)
    for name in ("latest.html", "index.html"):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(page)

    print(f"Hits: {len(hits)} · bars: {result.get('bars', 0)}", flush=True)
    if result.get("error"):
        print(f"Error: {result['error']}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
