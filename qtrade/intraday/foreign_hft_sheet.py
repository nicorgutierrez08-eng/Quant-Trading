"""Foreign HFT tracker: the minute-level strategies on foreign exchanges, logged in the sheet with
$0 allocated - not part of the $10,000 book.

``qtrade.research.foreign_hft`` found no minute-level strategy that beats the spread in any foreign
market, so none trades book money. This tracker still runs each market's pick from that study
(e.g. "reversal k=3 h=12": rank by the last 3 five-minute bars, hold 12) on every session's
5-minute bars after the close and writes every simulated trade window to the "Foreign HFT tracker"
tab, with its P&L in bp after the estimated spread and in dollars on a hypothetical $10,000 book split
equally between the markets - so the live record can be compared with the study.
"""
from __future__ import annotations

import json
import os
import re

import numpy as np
import pandas as pd

from ..research.foreign import MARKETS
from ..research.foreign_hft import SPREAD_BP, bars, simulate
from ..utils import LOG
from .foreign_sheet import CLOSE_UTC

TAB = "Foreign HFT tracker"
BOOK_USD = 10_000.0                               # hypothetical, split equally between the tracked markets
CLOSE = {**CLOSE_UTC, "Japan": 6 * 60 + 40}       # Tokyo isn't in the overnight sleeve but is tracked here
HEADER = ["Date", "Market", "Variant", "Entry (local)", "Exit (local)", "Longs", "Shorts", "Gross bp", "Spread bp",
          "Net bp", "P&L $"]


def parse_pick(pick: str) -> tuple[float, int, int]:
    """'reversal k=3 h=12' -> (sign, k, h)."""
    m = re.match(r"(reversal|momentum) k=(\d+) h=(\d+)", pick)
    if not m:
        raise ValueError(f"unknown pick {pick!r}")
    return (-1.0 if m.group(1) == "reversal" else 1.0), int(m.group(2)), int(m.group(3))


def session_rows(mkt: str, pick: str, o: pd.DataFrame, c: pd.DataFrame, day, notional: float) -> list[list]:
    """The simulated trade windows of ``day`` (bars of that session only)."""
    sign, k, h = parse_pick(pick)
    mask = np.array(o.index.date) == day
    if mask.sum() < k + h + 2:
        return []
    spread = SPREAD_BP.get(mkt, 5.0)
    p = simulate(o[mask], c[mask], k, h, sign, spread)
    return [[f"{day:%Y-%m-%d}", mkt, pick, f"{r.time:%H:%M}", f"{r.exit_time:%H:%M}", r.longs, r.shorts,
             round(r.gross * 1e4, 2), spread, round(r.net * 1e4, 2), round(notional * r.net, 2)]
            for r in p.itertuples()]


class TrackerSheet:
    def __init__(self, sheet_id: str, creds_json: str):
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
        self.s = AuthorizedSession(creds)
        self.base = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        meta = self.s.get(self.base, params={"fields": "sheets.properties.title"}, timeout=30).json()
        if TAB not in [x["properties"]["title"] for x in meta.get("sheets", [])]:
            self.s.post(f"{self.base}:batchUpdate", json={"requests": [{"addSheet": {"properties": {"title": TAB}}}]},
                        timeout=30).raise_for_status()

    def rows(self) -> list[list]:
        r = self.s.get(f"{self.base}/values/'{TAB}'!A6:K1000000", timeout=60)
        r.raise_for_status()
        return r.json().get("values", [])

    def write(self, new: list[list], summary: list[list], status: str) -> None:
        title = ("Foreign HFT tracker - $0 allocated, NOT part of the $10,000 book. Minute-level reversal / momentum "
                 "on 5-minute bars (each market's pick from the foreign_hft study, which found no edge after the "
                 "spread); P&L after an estimated spread, in dollars on a hypothetical $10,000 book split equally between the markets.")
        # the summary sits beside the trade rows: append without inserting rows (that would shift it down)
        if new:
            self.s.post(f"{self.base}/values/'{TAB}'!A6:K:append",
                        params={"valueInputOption": "RAW", "insertDataOption": "OVERWRITE"},
                        json={"values": new}, timeout=60).raise_for_status()
        self.s.post(f"{self.base}/values:batchClear", json={"ranges": [f"'{TAB}'!M6:R100000"]},
                    timeout=30).raise_for_status()
        data = [{"range": f"'{TAB}'!A1", "values": [[title]]}, {"range": f"'{TAB}'!A3", "values": [[status]]},
                {"range": f"'{TAB}'!A5:K5", "values": [HEADER]},
                {"range": f"'{TAB}'!M5:R{5 + len(summary)}", "values": summary}]
        self.s.post(f"{self.base}/values:batchUpdate", json={"valueInputOption": "RAW", "data": data},
                    timeout=30).raise_for_status()


def summarise(rows: list[list]) -> list[list]:
    head = [["Market", "Days", "Trades", "Avg net bp", "Days positive", "P&L $"]]
    if not rows:
        return head
    df = pd.DataFrame([r[:11] for r in rows if len(r) >= 11], columns=HEADER)
    df["Net bp"] = pd.to_numeric(df["Net bp"], errors="coerce")
    df["P&L $"] = pd.to_numeric(df["P&L $"], errors="coerce")
    out = []
    for m, g in df.groupby("Market"):
        daily = g.groupby("Date")["P&L $"].sum()
        out.append([m, int(daily.size), int(len(g)), round(float(g["Net bp"].mean()), 2),
                    round(float((daily > 0).mean()), 2), round(float(daily.sum()), 2)])
    daily = df.groupby("Date")["P&L $"].sum()
    out.append(["ALL", int(daily.size), int(len(df)), round(float(df["Net bp"].mean()), 2),
                round(float((daily > 0).mean()), 2), round(float(df["P&L $"].sum()), 2)])
    return head + out


def run(picks: dict[str, str], dry_run: bool = False) -> dict:
    now = pd.Timestamp.now(tz="UTC")
    today = now.tz_localize(None).normalize().date()
    sheet = None if dry_run else TrackerSheet(os.environ["HFT_SHEET_ID"], os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    old = sheet.rows() if sheet else []
    done = {(r[0], r[1]) for r in old if len(r) >= 2}
    new = []
    for mkt, pick in picks.items():
        if mkt not in MARKETS or now.hour * 60 + now.minute < CLOSE.get(mkt, 17 * 60) + 20:
            continue
        if (f"{today:%Y-%m-%d}", mkt) in done:
            continue
        try:
            o, c = bars(MARKETS[mkt], period="5d", interval="5m")
            new += session_rows(mkt, pick, o, c, today, BOOK_USD / len(picks))
        except Exception as exc:
            LOG.warning("tracker %s: %s", mkt, exc)
    summary = summarise(old + new)
    day_pnl = sum(r[10] for r in new)
    status = (f"Updated {now:%Y-%m-%d %H:%M} UTC - today {len(new)} simulated trades, ${day_pnl:+,.2f} on the hypothetical "
              f"$10,000 (${BOOK_USD / len(picks):,.2f} per market); since the start ${summary[-1][5] if len(summary) > 1 else 0:+,.2f}.")
    if sheet:
        sheet.write(new, summary, status)
    LOG.info("foreign HFT tracker: %s", status)
    return {"trades": len(new), "pnl": round(day_pnl, 2)}


def main(argv=None):
    import argparse

    from ..utils import setup_logging

    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="data/foreign_hft_rules.json", help="the study's picks")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    if pd.Timestamp.now(tz="UTC").weekday() >= 5:
        print({"skipped": "weekend"})
        return
    picks = {r["market"]: r["pick"] for r in json.load(open(args.rules))}
    print(run(picks, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
