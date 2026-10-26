"""Overnight persistence on foreign stock exchanges (Asia and Europe), as a sleeve of the simulated
$10,000 sheet book.

In each market (``MARKETS``: picked because the strategy worked there on 2006-2014, the period
that also fixed its direction - see ``qtrade.research.foreign``), long the fifth of 30-40 large
caps with the highest sum of overnight returns over the last 21 sessions and short the lowest
fifth, bought / sold at the official close and closed at the next official open. Dollar neutral
in each market, equal capital per market, 0 bp fees, nothing sent to any broker. Returns are in
local currency (each market's book is long and short the same currency, so the dollar exposure
is only its P&L).

Once a day after Europe closes (17:11 UTC) (``python -m qtrade.intraday.foreign_sheet``): every open book is
settled at the first official open after its entry, and each market that traded today opens
tonight's book at today's close. Prices are Yahoo's dividend-adjusted daily open and close, so a
dividend shows as income, not as an overnight drop. The sheet holds the state: a daily log in
the "Foreign book" tab, tonight's positions to the right, every round trip in "Foreign trades".
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from ..research.asia import _xs_weights
from ..research.foreign import MARKETS as STOCKS
from ..utils import LOG

TAB, TRADES_TAB = "Foreign book", "Foreign trades"
MARKETS = ["Hong Kong", "Korea", "Taiwan", "Australia", "India", "UK", "Germany", "France"]
# latest official close in UTC minutes (the later of summer / winter time), plus the closing auction
CLOSE_UTC = {"Hong Kong": 8 * 60 + 10, "Korea": 6 * 60 + 40, "Taiwan": 5 * 60 + 40, "Australia": 6 * 60 + 20,
             "India": 10 * 60 + 10, "UK": 16 * 60 + 40, "Germany": 16 * 60 + 40, "France": 16 * 60 + 45}
LOG_HEADER = ["Date", "Day P&L $", "Day %", "Equity $", "Markets settled", "Positions opened", "Gross $",
              "Capital $"]
HOLD_HEADER = ["Market", "Symbol", "Entry date", "Entry (official close)", "Position $"]
TRADE_HEADER = ["Market", "Symbol", "Side", "Entry date", "Entry price", "Exit date", "Exit price", "Position $",
                "P&L $", "Return %"]


def target_weights(open_: pd.DataFrame, close: pd.DataFrame) -> pd.Series:
    """Tonight's weights (gross 1, dollar neutral) from the last session in ``close``."""
    prev = close.shift(1)
    bad = (open_ == prev) | (open_ == close)            # Yahoo copied the previous close: no real open
    on = np.log(open_ / prev).mask(bad)
    sig = on.rolling(21, min_periods=15).sum().iloc[[-1]]
    sig = sig.sub(sig.mean(axis=1), axis=0)
    w = _xs_weights(sig).iloc[0]
    return w[w != 0]


def settle(hold: pd.DataFrame, opens: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Close every position whose market has opened since its entry date. Returns (trades, still held)."""
    rows, keep = [], []
    for h in hold.itertuples(index=False):
        o = opens.get(h.Market)
        px = None
        if o is not None and h.Symbol in o.columns:
            later = o[h.Symbol][o.index > pd.Timestamp(h._2)].dropna()
            if len(later):
                px = (later.index[0], float(later.iloc[0]))
        if px is None:
            keep.append(h)
            continue
        side = 1.0 if h._4 > 0 else -1.0
        r = px[1] / float(h._3) - 1
        rows.append([h.Market, h.Symbol, "long" if side > 0 else "short", h._2, round(float(h._3), 4),
                     f"{px[0]:%Y-%m-%d}", round(px[1], 4), round(abs(float(h._4)), 2), round(float(h._4) * r, 2),
                     round(100 * side * r, 3)])
    return pd.DataFrame(rows, columns=TRADE_HEADER), pd.DataFrame(keep, columns=HOLD_HEADER)


def open_books(data: dict[str, tuple[pd.DataFrame, pd.DataFrame]], day: pd.Timestamp, capital: float,
               held_markets: set) -> pd.DataFrame:
    """Tonight's positions in each market whose last session is ``day`` (and has no book open)."""
    live = [m for m, (o, c) in data.items() if len(c) and c.index[-1] == day and m not in held_markets]
    per = capital / len(MARKETS)
    rows = []
    for m in live:
        o, c = data[m]
        w = target_weights(o, c)
        last = c.iloc[-1]
        for t, x in w.items():
            if np.isfinite(last.get(t, np.nan)):
                rows.append([m, t, f"{day:%Y-%m-%d}", round(float(last[t]), 4), round(float(x * per), 2)])
    return pd.DataFrame(rows, columns=HOLD_HEADER)


def download(markets: list[str], now: pd.Timestamp | None = None) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    """Adjusted daily opens / closes; today's bar is dropped for a market whose session isn't over
    (Yahoo shows the latest price as today's "close" while the market is open)."""
    import yfinance as yf

    now = now or pd.Timestamp.now(tz="UTC")
    today = now.tz_localize(None).normalize()
    out = {}
    for m in markets:
        raw = yf.download(STOCKS[m], period="3mo", interval="1d", group_by="ticker", auto_adjust=True,
                          progress=False, threads=True)
        o = pd.DataFrame({t: raw[t]["Open"] for t in STOCKS[m] if t in raw.columns.get_level_values(0)})
        c = pd.DataFrame({t: raw[t]["Close"] for t in STOCKS[m] if t in raw.columns.get_level_values(0)})
        o.index = c.index = pd.to_datetime(c.index).tz_localize(None).normalize()
        live = c.notna().sum(axis=1) >= max(10, c.shape[1] // 3)
        o, c = o[live], c[live]
        if len(c) and c.index[-1] == today and now.hour * 60 + now.minute < CLOSE_UTC[m] + 20:
            o, c = o.iloc[:-1], c.iloc[:-1]
        out[m] = (o, c)
    return out


class ForeignSheet:
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
        log = self.get(TAB, "A6:H100000")
        hold = self.get(TAB, "J6:N5000")
        log = pd.DataFrame([r + [""] * (len(LOG_HEADER) - len(r)) for r in log], columns=LOG_HEADER) if log else \
            pd.DataFrame(columns=LOG_HEADER)
        hold = pd.DataFrame([r[:5] for r in hold if len(r) >= 5], columns=HOLD_HEADER) if hold else \
            pd.DataFrame(columns=HOLD_HEADER)
        for c in ("Entry (official close)", "Position $"):
            hold[c] = pd.to_numeric(hold[c], errors="coerce")
        return log, hold

    def write(self, status: str, log_row: list, n_log: int, holdings: pd.DataFrame, trades: pd.DataFrame) -> None:
        self.s.post(f"{self.base}/values:batchClear", json={"ranges": [f"'{TAB}'!J6:N5000"]},
                    timeout=30).raise_for_status()
        title = ("Foreign book sleeve - overnight persistence on foreign exchanges (" + ", ".join(MARKETS) + "): long "
                 "the top fifth / short the bottom fifth by the last 21 overnight returns, official close -> next "
                 "official open, 0 bp fees, nothing sent to a broker.")
        row = 6 + n_log
        data = [{"range": f"'{TAB}'!A1", "values": [[title]]}, {"range": f"'{TAB}'!A3", "values": [[status]]},
                {"range": f"'{TAB}'!A5:H5", "values": [LOG_HEADER]}, {"range": f"'{TAB}'!J5:N5", "values": [HOLD_HEADER]},
                {"range": f"'{TAB}'!A{row}:H{row}", "values": [log_row]},
                {"range": f"'{TRADES_TAB}'!A1:J1", "values": [TRADE_HEADER]}]
        if len(holdings):
            data.append({"range": f"'{TAB}'!J6:N{5 + len(holdings)}", "values": holdings.values.tolist()})
        self.s.post(f"{self.base}/values:batchUpdate", json={"valueInputOption": "RAW", "data": data},
                    timeout=30).raise_for_status()
        if len(trades):
            self.s.post(f"{self.base}/values/'{TRADES_TAB}'!A2:J:append",
                        params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                        json={"values": trades.values.tolist()}, timeout=60).raise_for_status()


def step(hold: pd.DataFrame, data: dict, day: pd.Timestamp, equity: float, deposit: float) -> dict:
    """Pure: settle, then open tonight's books on the new equity."""
    trades, still = settle(hold, {m: o for m, (o, c) in data.items()})
    pnl = float(trades["P&L $"].sum()) if len(trades) else 0.0
    eq = equity + deposit + pnl
    new = open_books(data, day, eq, set(still["Market"]))
    return {"trades": trades, "pnl": pnl, "equity": eq, "capital_base": equity + deposit,
            "holdings": pd.concat([still, new], ignore_index=True), "opened": len(new),
            "settled": sorted(set(trades["Market"])) if len(trades) else []}


def run(sleeve_usd: float, dry_run: bool = False) -> dict:
    now = pd.Timestamp.now(tz="UTC")
    day = now.tz_localize(None).normalize()
    sheet = None if dry_run else ForeignSheet(os.environ["HFT_SHEET_ID"], os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    log, hold = sheet.state() if sheet else (pd.DataFrame(columns=LOG_HEADER), pd.DataFrame(columns=HOLD_HEADER))
    if len(log) and str(log["Date"].iloc[-1]) == f"{day:%Y-%m-%d}":
        return {"skipped": "already booked today"}
    data = download(MARKETS)
    equity = float(pd.to_numeric(log["Equity $"], errors="coerce").dropna().iloc[-1]) if len(log) else 0.0
    cap = pd.to_numeric(log.get("Capital $", pd.Series(dtype=str)), errors="coerce").dropna()
    deposit = sleeve_usd - (float(cap.iloc[-1]) if len(cap) else 0.0)
    res = step(hold, data, day, equity, deposit)
    h = res["holdings"]
    row = [f"{day:%Y-%m-%d}", round(res["pnl"], 2),
           round(100 * res["pnl"] / res["capital_base"], 4) if res["capital_base"] else 0.0, round(res["equity"], 2),
           ", ".join(res["settled"]) or "-", res["opened"], round(float(h["Position $"].abs().sum()), 2) if len(h) else 0.0,
           round(sleeve_usd, 2)]
    total = res["equity"] - sleeve_usd
    status = (f"Updated {now:%Y-%m-%d %H:%M} UTC - capital ${sleeve_usd:,.2f} -> equity ${res['equity']:,.2f} "
              f"(P&L ${total:+,.2f}). Today: ${res['pnl']:+,.2f} from {', '.join(res['settled']) or 'no market'}; "
              f"{res['opened']} positions opened at today's closes.")
    if sheet:
        sheet.write(status, row, len(log), h, res["trades"])
    LOG.info("foreign sleeve: %s", status)
    return {"date": row[0], "pnl": row[1], "equity": row[3], "opened": row[5], "trades": len(res["trades"])}


def main(argv=None):
    import argparse

    from ..intraday.hft_shadow import book_split
    from ..utils import setup_logging

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    if pd.Timestamp.now(tz="UTC").weekday() >= 5:
        print({"skipped": "weekend"})
        return
    sleeve = book_split().get("foreign", 0.0)
    if sleeve <= 0:
        print({"skipped": "no money allocated to the foreign sleeve (config/sheet_book.json)"})
        return
    print(run(sleeve, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
