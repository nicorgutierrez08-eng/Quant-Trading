"""The auction strategies as a sleeve of the simulated $10,000 Google Sheet book.

The same books the Alpaca auction trader (``auction_live``) built, filled in the sheet at the
official auction prices instead of being sent to Alpaca (whose paper simulator left most
auction orders unfilled), with 0 bp fees:

* **overnight book** - ``last30_fade``, ``overnight_persistence`` and the ``last_reaction``
  earnings leg, decided from prices up to 15:45 (``auction_live.build_book``), bought / sold at
  the official close and closed at the next official open;
* **ADR book** - Asian ADRs against their home markets (``adr_book``), decided from the
  pre-market price before 9:25, opened at the official open and closed at the official close.

Once a day after the close (``python -m qtrade.intraday.auction_sheet``) the sleeve settles
last night's book at today's open and today's ADR book at today's close, then opens tonight's
book at today's close. Every decision uses only data stamped before the moment it would have
been made live (15:45 for the overnight book, 9:25 for the ADR book), so running after the close
changes nothing but the timing. The sheet holds the sleeve's state: a daily log in the
"Auction book" tab (row 6 down) with tonight's positions to the right, and every closed round
trip in the "Auction trades" tab.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

NY = "America/New_York"
TAB, TRADES_TAB = "Auction book", "Auction trades"
LOG_HEADER = ["Date", "Overnight P&L $", "ADR P&L $", "Day P&L $", "Day %", "Equity $", "Overnight longs",
              "Overnight shorts", "Overnight gross $", "ADR names", "Capital $"]
HOLD_HEADER = ["Symbol", "Shares", "Entry (official close)", "Position $"]
TRADE_HEADER = ["Book", "Symbol", "Side", "Shares", "Entry (NY)", "Entry price", "Exit (NY)", "Exit price",
                "Position $", "P&L $", "Return %"]


# --- pure book-keeping ---------------------------------------------------------------------------
def round_trips(book: str, shares: dict[str, float], entry: dict[str, float], exit_: dict[str, float],
                entry_time: str, exit_time: str) -> pd.DataFrame:
    """One row per position closed at ``exit_`` prices (a name with no exit price is closed flat)."""
    rows = []
    for t, q in shares.items():
        if q == 0 or not np.isfinite(entry.get(t, np.nan)):
            continue
        px_in = entry[t]
        px_out = exit_.get(t, np.nan)
        px_out = px_out if np.isfinite(px_out) else px_in
        pnl = q * (px_out - px_in)
        rows.append([book, t, "long" if q > 0 else "short", round(abs(q), 4), entry_time, round(px_in, 4), exit_time,
                     round(px_out, 4), round(abs(q) * px_in, 2), round(pnl, 2),
                     round(100 * np.sign(q) * (px_out / px_in - 1), 3)])
    return pd.DataFrame(rows, columns=TRADE_HEADER)


def shares_for(weights: dict[str, float], prices: dict[str, float], capital: float) -> dict[str, float]:
    """Fractional shares for target weights (fractions of capital) at ``prices``."""
    out = {}
    for t, w in weights.items():
        p = prices.get(t, np.nan)
        if abs(w) > 1e-9 and np.isfinite(p) and p > 0:
            out[t] = round(w * capital / p, 4)
    return out


def capital_so_far(log: pd.DataFrame) -> float:
    cap = pd.to_numeric(log.get("Capital $", pd.Series(dtype=str)), errors="coerce").dropna()
    return float(cap.iloc[-1]) if len(cap) else 0.0


# --- data ----------------------------------------------------------------------------------------
def _official(daily: dict[str, pd.DataFrame], day: pd.Timestamp, field: str) -> dict[str, float]:
    out = {}
    for t, f in daily.items():
        g = f[f.index.tz_convert(NY).tz_localize(None).normalize() == day]
        if len(g):
            out[t] = float(g[field].iloc[-1])
    return out


def day_inputs(cfg, tickers: list[str], signs: dict, day: pd.Timestamp) -> dict:
    """Everything the day needs, from Alpaca (consolidated daily bars, IEX intraday) and Yahoo."""
    from ..data.intraday import AlpacaBars
    from .adr_book import ADRS, build_targets, home_moves
    from .auction_live import _adr_prices, _earnings_reactions, _fetch, build_book

    acfg = cfg.auction
    data = AlpacaBars(feed=acfg.feed)
    start = day.tz_localize(NY)
    adr_names = [t for t, (_, _, m) in ADRS.items() if not acfg.adr_markets or m in acfg.adr_markets] \
        if acfg.adr_enabled else []
    syms = list(dict.fromkeys(tickers + adr_names))
    daily = _fetch(data, syms, "1Day", start - pd.Timedelta(days=45), pd.Timestamp.now(tz=NY) - pd.Timedelta(minutes=16),
                   "sip")
    today_5 = _fetch(data, tickers, "5Min", start + pd.Timedelta(hours=9, minutes=30),
                     start + pd.Timedelta(hours=15, minutes=45), acfg.feed)
    reactions = _earnings_reactions(data, acfg, tickers, day) if "last_reaction" in acfg.strategies else None
    book = build_book(today_5, daily, tickers, signs, acfg, day, None, reactions)
    adr_w, adr_tab = {}, pd.DataFrame()
    if adr_names:
        try:
            moves = home_moves(day, adr_names)
            if len(moves):
                names = list(moves["adr"])
                prev_close = {}
                for t in names:
                    f = daily.get(t)
                    if f is not None:
                        f = f[f.index.tz_convert(NY).tz_localize(None).normalize() < day]
                        if len(f):
                            prev_close[t] = float(f["close"].iloc[-1])
                ref = _adr_prices(data, names, day, start + pd.Timedelta(hours=9, minutes=25), after_open=False)
                ref = {t: ref.get(t, prev_close.get(t, np.nan)) for t in names}
                adr_w, adr_tab = build_targets(acfg, day, prev_close, ref, moves, None, acfg.adr_sign)
        except Exception as exc:
            LOG.warning("ADR book skipped today: %s", exc)
    return {"open": _official(daily, day, "open"), "close": _official(daily, day, "close"),
            "weights": {t: w for t, w in book["weights"].items() if abs(w) > 1e-9},
            "strategies": book["strategies"], "adr_weights": adr_w, "adr_table": adr_tab}


# --- the sheet -----------------------------------------------------------------------------------
class AuctionSheet:
    def __init__(self, sheet_id: str, creds_json: str):
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
        self.s = AuthorizedSession(creds)
        self.base = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        meta = self.s.get(self.base, params={"fields": "sheets.properties.title"}, timeout=30).json()
        have = [x["properties"]["title"] for x in meta.get("sheets", [])]
        new = [{"addSheet": {"properties": {"title": t}}} for t in (TAB, TRADES_TAB) if t not in have]
        if new:
            self.s.post(f"{self.base}:batchUpdate", json={"requests": new}, timeout=30).raise_for_status()

    def get(self, tab: str, rng: str) -> list[list]:
        r = self.s.get(f"{self.base}/values/'{tab}'!{rng}", timeout=30)
        r.raise_for_status()
        return r.json().get("values", [])

    def state(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        log = self.get(TAB, "A6:K100000")
        hold = self.get(TAB, "M6:P5000")
        log = pd.DataFrame([r + [""] * (len(LOG_HEADER) - len(r)) for r in log], columns=LOG_HEADER) if log else \
            pd.DataFrame(columns=LOG_HEADER)
        hold = pd.DataFrame([r[:4] for r in hold if len(r) >= 4], columns=HOLD_HEADER) if hold else \
            pd.DataFrame(columns=HOLD_HEADER)
        for c in HOLD_HEADER[1:]:
            hold[c] = pd.to_numeric(hold[c], errors="coerce")
        return log, hold

    def write(self, status: str, log_row: list, n_log: int, holdings: pd.DataFrame, trades: pd.DataFrame) -> None:
        row = 6 + n_log
        self.s.post(f"{self.base}/values:batchClear", json={"ranges": [f"'{TAB}'!M6:P5000"]},
                    timeout=30).raise_for_status()
        title = ("Auction book sleeve - the auction strategies filled at the official open / close in the sheet "
                 "(overnight: last30_fade + overnight_persistence + last_reaction, close -> next open; "
                 "ADR book: open -> close). 0 bp fees, nothing sent to Alpaca.")
        data = [{"range": f"'{TAB}'!A1", "values": [[title]]}, {"range": f"'{TAB}'!A3", "values": [[status]]},
                {"range": f"'{TAB}'!A5:K5", "values": [LOG_HEADER]}, {"range": f"'{TAB}'!M5:P5", "values": [HOLD_HEADER]},
                {"range": f"'{TAB}'!A{row}:K{row}", "values": [log_row]},
                {"range": f"'{TRADES_TAB}'!A1:K1", "values": [TRADE_HEADER]}]
        if len(holdings):
            data.append({"range": f"'{TAB}'!M6:P{5 + len(holdings)}", "values": holdings.values.tolist()})
        self.s.post(f"{self.base}/values:batchUpdate", json={"valueInputOption": "RAW", "data": data},
                    timeout=30).raise_for_status()
        if len(trades):
            self.s.post(f"{self.base}/values/'{TRADES_TAB}'!A2:K:append",
                        params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                        json={"values": trades.values.tolist()}, timeout=60).raise_for_status()


def settle_day(day: str, inputs: dict, prev_hold: pd.DataFrame, equity: float, deposit: float,
               adr_gross_capital: float | None = None) -> dict:
    """Pure: settle last night's book at today's open, today's ADR book at today's close, open
    tonight's book at today's close. Returns the trades, P&L, new equity and tonight's holdings."""
    o, c = inputs["open"], inputs["close"]
    prev = dict(zip(prev_hold["Symbol"], prev_hold["Shares"])) if len(prev_hold) else {}
    prev_px = dict(zip(prev_hold["Symbol"], prev_hold["Entry (official close)"])) if len(prev_hold) else {}
    last_day = prev_hold.attrs.get("date", "previous close")
    night = round_trips("overnight", prev, prev_px, o, f"{last_day} 16:00", f"{day} 09:30")
    cap = equity + deposit
    adr_sh = shares_for(inputs["adr_weights"], o, adr_gross_capital or cap)
    adr = round_trips("ADR", adr_sh, o, c, f"{day} 09:30", f"{day} 16:00")
    pnl_n = float(night["P&L $"].sum()) if len(night) else 0.0
    pnl_a = float(adr["P&L $"].sum()) if len(adr) else 0.0
    eq = cap + pnl_n + pnl_a
    tonight = shares_for(inputs["weights"], c, eq)
    hold = pd.DataFrame({"Symbol": list(tonight), "Shares": list(tonight.values()),
                         "Entry (official close)": [round(c[t], 4) for t in tonight],
                         "Position $": [round(q * c[t], 2) for t, q in tonight.items()]}, columns=HOLD_HEADER)
    return {"trades": pd.concat([night, adr], ignore_index=True), "pnl_overnight": pnl_n, "pnl_adr": pnl_a,
            "equity": eq, "capital_base": cap, "holdings": hold.sort_values("Position $", ascending=False),
            "adr_names": len(adr)}


def run(sleeve_usd: float, cfg, tickers: list[str], signs: dict, dry_run: bool = False) -> dict:
    now = pd.Timestamp.now(tz=NY)
    day = now.tz_localize(None).normalize()
    sheet = None if dry_run else AuctionSheet(os.environ["HFT_SHEET_ID"], os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    log, hold = sheet.state() if sheet else (pd.DataFrame(columns=LOG_HEADER), pd.DataFrame(columns=HOLD_HEADER))
    if len(log) and str(log["Date"].iloc[-1]) == f"{day:%Y-%m-%d}":
        return {"skipped": "already booked today"}
    inputs = day_inputs(cfg, tickers, signs, day)
    if len(inputs["close"]) < 0.5 * len(tickers):
        return {"skipped": f"only {len(inputs['close'])} official closes today - market closed or data late"}
    if len(log):
        hold.attrs["date"] = str(log["Date"].iloc[-1])
    equity = float(pd.to_numeric(log["Equity $"], errors="coerce").dropna().iloc[-1]) if len(log) else 0.0
    deposit = sleeve_usd - capital_so_far(log)
    res = settle_day(f"{day:%Y-%m-%d}", inputs, hold, equity, deposit)
    h = res["holdings"]
    day_pnl = res["pnl_overnight"] + res["pnl_adr"]
    row = [f"{day:%Y-%m-%d}", round(res["pnl_overnight"], 2), round(res["pnl_adr"], 2), round(day_pnl, 2),
           round(100 * day_pnl / res["capital_base"], 4) if res["capital_base"] else 0.0, round(res["equity"], 2),
           int((h["Shares"] > 0).sum()), int((h["Shares"] < 0).sum()), round(float(h["Position $"].abs().sum()), 2),
           res["adr_names"], round(sleeve_usd, 2)]
    total = res["equity"] - sleeve_usd
    status = (f"Updated {now:%Y-%m-%d %H:%M} New York - capital ${sleeve_usd:,.2f} -> equity ${res['equity']:,.2f} "
              f"(P&L ${total:+,.2f}). Today: overnight book ${res['pnl_overnight']:+,.2f}, ADR book "
              f"${res['pnl_adr']:+,.2f}. Tonight: {row[6]} long / {row[7]} short, ${row[8]:,.0f} gross "
              f"(strategies: {', '.join(inputs['strategies']) or 'none'}).")
    if sheet:
        sheet.write(status, row, len(log), h, res["trades"])
    LOG.info("auction sleeve: %s", status)
    return {"date": row[0], "pnl": row[3], "equity": row[5], "longs": row[6], "shorts": row[7], "trades": len(res["trades"])}


def main(argv=None):
    import argparse

    from ..config import Config
    from ..intraday.hft_shadow import book_split
    from ..utils import setup_logging
    from .auction_live import load_inputs

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/auction_paper.yaml")
    ap.add_argument("--tickers", default="data/auction_tickers.json")
    ap.add_argument("--signs", default="data/auction_signs.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="run outside 16:20-24:00 New York")
    args = ap.parse_args(argv)
    setup_logging()
    now = pd.Timestamp.now(tz=NY)
    if not args.force and not (now.weekday() < 5 and 16 * 60 + 20 <= now.hour * 60 + now.minute < 24 * 60):
        print({"skipped": f"outside the window ({now:%H:%M} NY)"})
        return
    sleeve = book_split().get("auction", 0.0)
    if sleeve <= 0:
        print({"skipped": "no money allocated to the auction sleeve (config/sheet_book.json)"})
        return
    cfg = Config.load(args.config)
    tickers, signs = load_inputs(args.tickers, args.signs if Path(args.signs).exists() else None)
    print(run(sleeve, cfg, tickers, signs, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
