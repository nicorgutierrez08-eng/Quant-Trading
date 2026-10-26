"""Nico's momentum flip as a sleeve of the simulated $10,000 Google Sheet book.

The rule (Nico's research_night; independently checked in ``qtrade.research.flip_check``,
net Sharpe 0.67 / 0.74 / 0.23 in 2006-14 / 2015-20 / 2021-26, and 0.53 before costs on a
point-in-time universe including delisted stocks):

* score = average of the cross-sectional percentile ranks of 12-1 month momentum and
  nearness to the 52-week high, over the largest ~1,000 US stocks priced at $5 or more;
* weights proportional to the demeaned score, dollar neutral, unit gross;
* held *short* (the whole book flipped) when the VIX closed above 20 the day before;
* rebalanced every 21 days, staggered: 21 sub-books each rebalance on their own day, so the
  book is the average of the targets set over the last 21 sessions.

Like the HFT sheet, nothing is traded on Alpaca: once a day, near the close, the sleeve is marked
to the latest prices (0 bp fees, instant execution), the day's P&L is booked and the new
holdings are written to the sheet's "Momentum flip" tab: a daily log from row 6 and the current
holdings to the right. The holdings in the sheet are the sleeve's only state.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

NY = "America/New_York"
TAB = "Momentum flip"
VIX_FLIP = 20.0
EVERY = 21
UNIVERSE_SIZE = 1000
LOG_HEADER = ["Date", "VIX (prev close)", "Regime", "Longs", "Shorts", "Gross $", "Day P&L $", "Day %", "Equity $",
              "Turnover $", "Capital $"]
HOLD_HEADER = ["Symbol", "Weight", "Position $", "Mark price"]


# --- the rule ------------------------------------------------------------------------------------
def scores(close: pd.DataFrame) -> pd.DataFrame:
    """Close-only momentum composite (the survivorship check's version of Nico's signal)."""
    lr = np.log(close / close.shift(1)).clip(-0.7, 0.7)
    mom = lr.rolling(231, min_periods=200).sum().shift(21)
    high = np.log(close / close.rolling(252, min_periods=200).max())
    ok = close >= 5
    return (mom.where(ok).rank(axis=1, pct=True) + high.where(ok).rank(axis=1, pct=True)) / 2


def unit_weights(z: pd.Series) -> pd.Series:
    s = z.dropna()
    s = s - s.mean()
    g = s.abs().sum()
    return s / g if g > 0 else s * 0.0


def target(close: pd.DataFrame, vix_prev: pd.Series) -> tuple[pd.Series, float]:
    """Today's staggered book (weights summing to 0, gross ~1) and today's sign."""
    z = scores(close)
    days = close.index[-EVERY:]
    books = []
    for d in days:
        sign = -1.0 if vix_prev.get(d, np.nan) > VIX_FLIP else 1.0
        books.append(unit_weights(z.loc[d]) * sign)
    w = pd.concat(books, axis=1).fillna(0.0).mean(axis=1)
    return w[w.abs() > 1e-6], (-1.0 if vix_prev.get(days[-1], np.nan) > VIX_FLIP else 1.0)


# --- data ----------------------------------------------------------------------------------------
def universe() -> list[str]:
    from ..data.universe import candidates_from_ishares, candidates_from_wikipedia

    try:
        c = candidates_from_ishares("ishares_r3000").sort_values("market_value", ascending=False)
    except Exception as exc:
        LOG.warning("iShares holdings unavailable (%s); S&P 1500 instead", exc)
        c = candidates_from_wikipedia()
    return [t for t in c["ticker"].astype(str) if t and t.lower() != "nan"][:UNIVERSE_SIZE]


def prices_and_vix(tickers: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Two years of daily closes (today's latest price as today's close) and the VIX close of the
    previous session for each day."""
    from ..data.loader import download_prices

    start = (pd.Timestamp.now(tz=NY) - pd.Timedelta(days=760)).strftime("%Y-%m-%d")
    md = download_prices(tickers + ["^VIX"], start=start)
    close = md.close
    close.index = pd.to_datetime(close.index).tz_localize(None)
    vix = close.pop("^VIX") if "^VIX" in close else pd.Series(dtype=float)
    return close.dropna(how="all"), vix.ffill().shift(1)


# --- the sheet -----------------------------------------------------------------------------------
class FlipSheet:
    def __init__(self, sheet_id: str, creds_json: str):
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
        self.s = AuthorizedSession(creds)
        self.base = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        meta = self.s.get(self.base, params={"fields": "sheets.properties.title"}, timeout=30).json()
        if TAB not in [x["properties"]["title"] for x in meta.get("sheets", [])]:
            r = self.s.post(f"{self.base}:batchUpdate", json={"requests": [{"addSheet": {"properties": {"title": TAB}}}]},
                            timeout=30)
            r.raise_for_status()

    def get(self, rng: str) -> list[list]:
        r = self.s.get(f"{self.base}/values/'{TAB}'!{rng}", timeout=30)
        r.raise_for_status()
        return r.json().get("values", [])

    def state(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        log = self.get("A6:K100000")
        hold = self.get("L6:O5000")
        log = pd.DataFrame([r + [""] * (len(LOG_HEADER) - len(r)) for r in log], columns=LOG_HEADER) if log else \
            pd.DataFrame(columns=LOG_HEADER)
        hold = pd.DataFrame([r[:4] for r in hold if len(r) >= 4], columns=HOLD_HEADER) if hold else \
            pd.DataFrame(columns=HOLD_HEADER)
        for c in ("Weight", "Position $", "Mark price"):
            hold[c] = pd.to_numeric(hold[c], errors="coerce")
        return log, hold

    def write(self, title: str, status: str, log_row: list, n_log: int, holdings: pd.DataFrame) -> None:
        row = 6 + n_log
        r = self.s.post(f"{self.base}/values:batchClear", json={"ranges": [f"'{TAB}'!L6:O5000"]}, timeout=30)
        r.raise_for_status()
        data = [{"range": f"'{TAB}'!A1", "values": [[title]]}, {"range": f"'{TAB}'!A3", "values": [[status]]},
                {"range": f"'{TAB}'!A5:K5", "values": [LOG_HEADER]}, {"range": f"'{TAB}'!L5:O5", "values": [HOLD_HEADER]},
                {"range": f"'{TAB}'!L6:O{6 + len(holdings)}", "values": holdings.values.tolist()}]
        data.append({"range": f"'{TAB}'!A{row}:K{row}", "values": [log_row]})
        r = self.s.post(f"{self.base}/values:batchUpdate", json={"valueInputOption": "RAW", "data": data}, timeout=30)
        r.raise_for_status()


def step(prev_hold: pd.DataFrame, equity: float, close: pd.DataFrame, w: pd.Series) -> tuple[float, float, pd.DataFrame]:
    """Mark the old holdings to today's prices, then rebalance to ``w``. Returns (day P&L, turnover $, new holdings)."""
    last = close.ffill().iloc[-1]
    pnl = 0.0
    old = pd.Series(dtype=float)
    if len(prev_hold):
        h = prev_hold.set_index("Symbol")
        px = last.reindex(h.index)
        r = (px / h["Mark price"] - 1).fillna(0.0)          # a name with no price today: flat
        pnl = float((h["Position $"] * r).sum())
        old = h["Position $"] * (1 + r)
    eq = equity + pnl
    pos = (w * eq).reindex(w.index)
    pos = pos[last.reindex(pos.index).notna()]
    turnover = float(pos.sub(old, fill_value=0.0).abs().sum())
    hold = pd.DataFrame({"Symbol": pos.index, "Weight": (pos / eq).round(6).values, "Position $": pos.round(2).values,
                         "Mark price": last.reindex(pos.index).round(4).values})
    return pnl, turnover, hold.sort_values("Weight", ascending=False).reset_index(drop=True)


def capital_so_far(log: pd.DataFrame) -> float:
    """The capital the sleeve held on its last booked day (the first rows predate the column: their start)."""
    cap = pd.to_numeric(log.get("Capital $", pd.Series(dtype=str)), errors="coerce").dropna()
    if len(cap):
        return float(cap.iloc[-1])
    first = log.iloc[0]
    return float(pd.to_numeric(first["Equity $"]) - pd.to_numeric(first["Day P&L $"]))


def run(sleeve_usd: float, dry_run: bool = False) -> dict:
    now = pd.Timestamp.now(tz=NY)
    today = now.strftime("%Y-%m-%d")
    close, vix_prev = prices_and_vix(universe())
    if close.index[-1].strftime("%Y-%m-%d") != today:
        LOG.info("flip sleeve: no prices dated today (%s) - market closed?", close.index[-1].date())
        return {"skipped": "no session today"}
    w, sign = target(close, vix_prev)
    sheet = None if dry_run else FlipSheet(os.environ["HFT_SHEET_ID"], os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    log, hold = sheet.state() if sheet else (pd.DataFrame(columns=LOG_HEADER), pd.DataFrame(columns=HOLD_HEADER))
    if len(log) and str(log["Date"].iloc[-1]) == today:
        return {"skipped": "already booked today"}
    equity = float(pd.to_numeric(log["Equity $"], errors="coerce").dropna().iloc[-1]) if len(log) else sleeve_usd
    deposit = sleeve_usd - capital_so_far(log) if len(log) else 0.0   # money moved in (or out) of the sleeve
    pnl, turnover, new_hold = step(hold, equity + deposit, close, w)
    eq = equity + deposit + pnl
    vix = float(vix_prev.iloc[-1]) if len(vix_prev) and np.isfinite(vix_prev.iloc[-1]) else float("nan")
    row = [today, round(vix, 2), "long momentum" if sign > 0 else "SHORT momentum (VIX > 20)",
           int((w > 0).sum()), int((w < 0).sum()), round(float(new_hold["Position $"].abs().sum()), 2),
           round(pnl, 2), round(100 * pnl / (equity + deposit), 4) if equity + deposit else 0.0, round(eq, 2), round(turnover, 2), round(sleeve_usd, 2)]
    total = eq - sleeve_usd
    status = (f"Updated {now:%Y-%m-%d %H:%M} New York - capital ${sleeve_usd:,.0f} -> equity ${eq:,.2f} "
              f"(P&L ${total:+,.2f}, {100 * total / sleeve_usd:+.2f}%). Today: VIX prev close {vix:.1f} -> "
              f"{'long' if sign > 0 else 'short'} momentum for the sub-book rebalanced today; book = average of the "
              f"last 21 sub-books. Marked at the latest price near the close, 0 bp fees, nothing sent to Alpaca.")
    title = "Momentum flip sleeve (Nico's rule: 12-1 momentum + 52-week high, short when VIX > 20, 21-day staggered)"
    if sheet:
        sheet.write(title, status, row, len(log), new_hold)
    LOG.info("flip sleeve: %s", status)
    return {"date": today, "pnl": round(pnl, 2), "equity": round(eq, 2), "longs": row[3], "shorts": row[4],
            "regime": row[2]}


def main(argv=None):
    import argparse

    from ..intraday.hft_shadow import book_split
    from ..utils import setup_logging

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="run outside 15:40-24:00 New York")
    args = ap.parse_args(argv)
    setup_logging()
    now = pd.Timestamp.now(tz=NY)
    if not args.force and not (now.weekday() < 5 and 15 * 60 + 40 <= now.hour * 60 + now.minute < 24 * 60):
        print({"skipped": f"outside the window 15:40-24:00 ({now:%H:%M} NY)"})
        return
    sleeve = book_split().get("momentum_flip", 0.0)
    if sleeve <= 0:
        print({"skipped": "no money allocated to the momentum flip sleeve (config/sheet_book.json)"})
        return
    print(run(sleeve, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
