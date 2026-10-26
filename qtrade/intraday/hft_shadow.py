"""Shadow high-frequency trader: simulated trades on live quotes, every one of them logged.

Nothing here touches the Alpaca account; Alpaca only supplies the live IEX quotes and
trades (its free real-time feed). The simulation is event-driven: every quote update and
trade is replayed in time order, decisions are made the moment the data arrives, and
every order reaches the market ``latency`` later (5 ms + up to 5 ms of random jitter by
default) - it executes at the price quoted *then*, not at the decision. Fees are 0 bp.

Rule set 2 (2026-10-22, after the first 2,300 trades lost ~5 bp each, ~4 bp of it the
spread paid on the way out):

* **passive exits** - every position closes with a resting order on the far side of the
  book (a long sells at the ask, a short buys at the bid), collecting the spread instead
  of paying it; only if it hasn't filled after ``Rules.exit_timeout_s`` does it cross the
  spread (column "Exit by": passive / market);
* **one position per stock per strategy** - no new orders in a stock the strategy is
  already in, which cuts turnover;
* ``imbalance_taker`` - only on a very lopsided book (|imbalance| >= 0.8) with a tight
  spread (<= 2 bp): buy at the ask / sell at the bid in the direction of the imbalance;
* ``imbalance_fade`` - the same trigger, the opposite direction (the first rule set's
  taker lost even at the midquote, so the signal may point the other way);
* ``market_maker`` - every 10 s, one order at the best bid and one at the best ask, live
  for 10 s once they arrive; a resting order fills when a trade prints at or through its
  price; the first fill cancels the other side;
* ``maker_with_signal`` - the same, quoting only the side the imbalance favours.

Rule set 3 (from 2026-10-23): ``qtrade.research.hft_replay`` replays recorded IEX data
through this simulator for a grid of rule variants (exit target, timeout, stop, imbalance
threshold, minimum maker spread), picks each strategy's rules on the first half of the days
and tests them on the second; ``config/hft_rules.json`` holds the picks, and only strategies
that made money on the test days trade. A fifth strategy, ``imbalance_flip``, is Nico's
momentum flip brought to the order book: follow the imbalance when yesterday's VIX closed at
or below 20, fade it above. Without the rules file, rule set 2 applies.

The HFT sleeve of the $10,000 sheet book (``config/sheet_book.json``; the rest is the momentum
flip sleeve, ``qtrade.intraday.flip_sleeve``) is split equally between the strategies that
trade; each position takes 1/10 of its strategy's equity. IEX's own book is thinner and wider than the national best bid
and offer. With ``GOOGLE_SERVICE_ACCOUNT_JSON`` and ``HFT_SHEET_ID`` set, new trades and
the summary go straight into the Google Sheet's "HFT trades" tab every few seconds.
"""
from __future__ import annotations

import json
import os
import random
import time
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.loader import to_alpaca
from ..utils import LOG

NY = "America/New_York"
QUOTES_URL = "https://data.alpaca.markets/v2/stocks/quotes"
TRADES_URL = "https://data.alpaca.markets/v2/stocks/trades"
SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "META", "AMD", "BAC"]
FEE_BP = 0.0                    # the sheet's assumption: no fees at all
LATENCY_MS = 5.0                # every order reaches the market this long after the decision ...
JITTER_MS = 5.0                 # ... plus a uniform random 0-5 ms
MAX_SPREAD_BP = 25.0            # ignore broken / one-sided IEX quotes (e.g. a 328 bp TSLA quote on 2026-10-22)
BOOK_USD = 10_000.0             # the whole simulated book
ALL_STRATEGIES = ["imbalance_taker", "imbalance_fade", "imbalance_flip", "market_maker", "maker_with_signal"]
SLOTS = 50                      # positions a strategy can hold at once: each takes 1/50 of its equity
NEVER = pd.Timestamp.max.tz_localize("UTC")


@dataclass(frozen=True)
class Rules:
    """Everything the strategies decide with. The defaults are rule set 2."""
    imb_threshold: float = 0.8          # takers: only a very lopsided book ...
    taker_max_spread_bp: float = 2.0    # ... with a tight spread
    taker_target: float = 0.0           # taker exits rest this many spreads beyond the entry (0 = at the entry)
    maker_target: float = 1.0           # maker exits: 1 = the far side of the book at the fill
    exit_timeout_s: float = 30.0        # a passive exit not filled by then crosses the spread
    stop_bp: float | None = None        # ... or as soon as the mid has moved this far against the position
    mm_every_s: float = 10.0
    mm_wait_s: float = 10.0
    mm_min_ticks: int = 1               # makers quote only when the spread is at least this many cents
    vix_flip: float = 20.0              # imbalance_flip follows the imbalance below this VIX, fades it above
    strategies: tuple = ("imbalance_taker", "imbalance_fade", "market_maker", "maker_with_signal")


RULES = Rules()
STRATEGIES = list(RULES.strategies)
RULES_FILE = Path(__file__).resolve().parents[2] / "config" / "hft_rules.json"
BOOK_FILE = Path(__file__).resolve().parents[2] / "config" / "sheet_book.json"


def book_split(path: Path = BOOK_FILE) -> dict[str, float]:
    """How the $10,000 sheet book is divided between the HFT sleeve and the momentum flip sleeve."""
    try:
        return {k: float(v) for k, v in json.loads(Path(path).read_text()).items() if not k.startswith("_")}
    except FileNotFoundError:
        return {"hft": BOOK_USD, "momentum_flip": 0.0}


def load_rules(path: Path = RULES_FILE, include_disabled: bool = False) -> dict[str, Rules]:
    """Per-strategy rules chosen by the replay (``qtrade.research.hft_replay``); only enabled strategies
    (or every pick with ``include_disabled``, for the $0 tracker). Without the file: rule set 2."""
    try:
        chosen = json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {k: replace(RULES, strategies=(k,)) for k in RULES.strategies}
    fields = set(Rules.__dataclass_fields__) - {"strategies"}
    return {k: Rules(**{f: v for f, v in c["rules"].items() if f in fields}, strategies=(k,))
            for k, c in chosen.items() if c.get("enabled") or (include_disabled and "rules" in c)}
COLUMNS = ["strategy", "symbol", "side", "decision_time", "entry_time", "entry_price", "exit_time", "exit_price",
           "notional", "pnl_usd", "pnl_mid_usd", "pnl_bp", "pnl_mid_bp", "spread_bp", "imbalance", "latency_ms",
           "exit_by"]


class Book:
    """Latest IEX top of book for one symbol."""

    def __init__(self):
        self.bid = self.ask = np.nan
        self.bsize = self.asize = np.nan

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def ok(self) -> bool:
        return bool(np.isfinite(self.bid) and np.isfinite(self.ask) and self.ask > self.bid > 0
                    and self.bsize > 0 and self.asize > 0)

    @property
    def imbalance(self) -> float:
        return float((self.bsize - self.asize) / (self.bsize + self.asize)) if self.ok else np.nan

    @property
    def spread_bp(self) -> float:
        return float((self.ask - self.bid) / self.mid * 1e4) if self.ok else np.nan


class ShadowHFT:
    """Event-driven state machine. Feed it quotes and trades in time order; orders execute after
    the latency at the book prevailing then."""

    def __init__(self, symbols: list[str], latency_ms: float = LATENCY_MS, jitter_ms: float = JITTER_MS,
                 seed: int = 0, equity: dict[str, float] | None = None, rules: Rules = RULES,
                 vix: float | None = None, book_usd: float = BOOK_USD):
        self.rules, self.vix = rules, vix
        self.books = {s: Book() for s in symbols}
        self.latency_ms, self.jitter_ms = latency_ms, jitter_ms
        self.rng = random.Random(seed)
        # the $10,000 book is split equally between the strategies; each strategy's equity moves with its
        # realised P&L, and cash is reserved when an order is sent and released when the position closes
        self.equity = dict(equity) if equity else {k: book_usd / len(rules.strategies) for k in rules.strategies}
        self.reserved: dict[str, float] = defaultdict(float)
        self.pending: list[dict] = []              # market orders on their way (entries and timed-out exits)
        self.resting: list[dict] = []              # maker entry orders
        self.positions: list[dict] = []            # open positions, each with a resting exit order
        self.closed: list[dict] = []
        self.busy: set[tuple[str, str]] = set()    # (strategy, symbol) with an order or a position
        self.last_mm: dict[str, pd.Timestamp] = defaultdict(lambda: pd.Timestamp(0, tz="UTC"))
        self._next_due = NEVER                     # earliest pending order / exit deadline (skips idle scans)

    def _delay(self) -> pd.Timedelta:
        return pd.Timedelta(milliseconds=self.latency_ms + self.rng.uniform(0, self.jitter_ms))

    def _reserve(self, strategy: str) -> float | None:
        if strategy not in self.equity:
            return None                                # strategy switched off
        size = self.equity[strategy] / SLOTS
        if size <= 0 or self.equity[strategy] - self.reserved[strategy] < size * 0.999:
            return None                                # all of this strategy's money is in use
        self.reserved[strategy] += size
        return size

    def _due(self, ts: pd.Timestamp) -> None:
        if ts < self._next_due:
            self._next_due = ts

    def _release(self, strategy: str, size: float) -> None:
        self.reserved[strategy] = max(0.0, self.reserved[strategy] - size)

    # --- positions --------------------------------------------------------------------------------
    def _open(self, o: dict, t: pd.Timestamp, price: float) -> None:
        """A filled entry: rest the exit on the far side of the book (after the latency)."""
        b, r = self.books[o["symbol"]], self.rules
        d = 1.0 if o["side"] == "buy" else -1.0
        k = r.maker_target if o["strategy"] in ("market_maker", "maker_with_signal") else r.taker_target
        spread = (b.ask - b.bid) if b.ok else 0.01
        exit_px = round(price + d * max(k * spread, 0.0), 2)
        if k > 0 and exit_px == price:
            exit_px = round(price + d * 0.01, 2)
        self.positions.append({**o, "entry_time": t, "entry_price": price, "exit_px": exit_px,
                               "exit_live_at": t + self._delay(),
                               "deadline": t + pd.Timedelta(seconds=r.exit_timeout_s)})
        self._due(self.positions[-1]["deadline"])

    def _close(self, p: dict, t: pd.Timestamp, exit_px: float, how: str) -> None:
        b = self.books[p["symbol"]]
        d = 1.0 if p["side"] == "buy" else -1.0
        pnl_bp = d * (exit_px / p["entry_price"] - 1) * 1e4 - FEE_BP
        mid = b.mid if b.ok else exit_px
        pnl_mid_bp = d * (mid / p["entry_price"] - 1) * 1e4 - FEE_BP
        pnl_usd = p["notional"] * pnl_bp / 1e4
        self.equity[p["strategy"]] += pnl_usd
        self._release(p["strategy"], p["notional"])
        self.busy.discard((p["strategy"], p["symbol"]))
        self.closed.append({"strategy": p["strategy"], "symbol": p["symbol"], "side": p["side"],
                            "decision_time": p["decision_time"], "entry_time": p["entry_time"],
                            "entry_price": p["entry_price"], "exit_time": t, "exit_price": exit_px,
                            "notional": p["notional"], "pnl_usd": pnl_usd, "pnl_mid_usd": p["notional"] * pnl_mid_bp / 1e4,
                            "pnl_bp": pnl_bp, "pnl_mid_bp": pnl_mid_bp, "spread_bp": p["spread_bp"],
                            "imbalance": p["imbalance"], "latency_ms": p["latency_ms"], "exit_by": how})

    # --- time ------------------------------------------------------------------------------------
    def advance(self, t: pd.Timestamp) -> None:
        """Everything due strictly before ``t`` happens against the book as it stands."""
        if t <= self._next_due:
            return
        while True:
            due = [(o["exec_at"], 0, i) for i, o in enumerate(self.pending) if o["exec_at"] < t] + \
                  [(p["deadline"], 1, i) for i, p in enumerate(self.positions) if p["deadline"] < t]
            if not due:
                break
            _, kind, i = min(due, key=lambda d: (d[0], d[1]))
            if kind == 1:                             # passive exit timed out: cross the spread
                p = self.positions.pop(i)
                self.pending.append({**p, "kind": "exit", "exec_at": p["deadline"] + self._delay()})
                continue
            o = self.pending.pop(i)
            b = self.books[o["symbol"]]
            if not b.ok:
                if o["kind"] == "entry":
                    self._release(o["strategy"], o["notional"])
                    self.busy.discard((o["strategy"], o["symbol"]))
                else:                                 # no book right now: try again a second later
                    self.pending.append({**o, "exec_at": o["exec_at"] + pd.Timedelta(seconds=1)})
                continue
            if o["kind"] == "entry":
                self._open(o, o["exec_at"], b.ask if o["side"] == "buy" else b.bid)
            else:
                self._close(o, o["exec_at"], b.bid if o["side"] == "buy" else b.ask, "market")
        self._next_due = min([o["exec_at"] for o in self.pending] + [p["deadline"] for p in self.positions],
                             default=NEVER)

    # --- inputs -----------------------------------------------------------------------------------
    def on_quote(self, sym: str, t: pd.Timestamp, bid: float, bsize: float, ask: float, asize: float) -> None:
        self.advance(t)
        b = self.books[sym]
        if not (bid > 0 and ask > bid and bsize > 0 and asize > 0):
            return
        b.bid, b.bsize, b.ask, b.asize = bid, bsize, ask, asize
        r = self.rules
        if r.stop_bp is not None:                     # stop: the mid moved too far against a position
            for p in [p for p in self.positions if p["symbol"] == sym and t >= p["exit_live_at"]]:
                d = 1.0 if p["side"] == "buy" else -1.0
                if d * (b.mid / p["entry_price"] - 1) * 1e4 <= -r.stop_bp:
                    self.positions.remove(p)
                    self.pending.append({**p, "kind": "exit", "exec_at": t + self._delay()})
                    self._due(self.pending[-1]["exec_at"])
        imb = b.imbalance
        if abs(imb) < r.imb_threshold or b.spread_bp > r.taker_max_spread_bp:
            return
        follow, fade = ("buy", "sell") if imb > 0 else ("sell", "buy")
        flip = fade if (self.vix is not None and self.vix > r.vix_flip) else follow
        for strategy, side in (("imbalance_taker", follow), ("imbalance_fade", fade), ("imbalance_flip", flip)):
            if (strategy, sym) in self.busy:
                continue
            size = self._reserve(strategy)
            if size is None:
                continue
            delay = self._delay()
            self.busy.add((strategy, sym))
            self.pending.append({"kind": "entry", "strategy": strategy, "symbol": sym, "side": side,
                                 "notional": size, "decision_time": t, "exec_at": t + delay,
                                 "spread_bp": b.spread_bp, "imbalance": imb,
                                 "latency_ms": delay.total_seconds() * 1e3})
            self._due(t + delay)

    def on_trade(self, sym: str, t: pd.Timestamp, price: float, size: float) -> None:
        self.advance(t)
        for p in list(self.positions):                # resting exits
            if p["symbol"] != sym or t < p["exit_live_at"]:
                continue
            if (p["side"] == "buy" and price >= p["exit_px"]) or (p["side"] == "sell" and price <= p["exit_px"]):
                self.positions.remove(p)
                self._close(p, t, p["exit_px"], "passive")
        for o in list(self.resting):                  # resting maker entries
            if o not in self.resting or o["symbol"] != sym or t < o["live_at"] or t > o["expires"]:
                continue
            if (o["side"] == "buy" and price <= o["price"]) or (o["side"] == "sell" and price >= o["price"]):
                self.resting.remove(o)
                for other in [x for x in self.resting if x["strategy"] == o["strategy"] and x["symbol"] == sym]:
                    self.resting.remove(other)        # first fill cancels the other side
                    self._release(other["strategy"], other["notional"])
                self._open(o, t, o["price"])

    def step(self, now: pd.Timestamp) -> None:
        """Clock tick: run everything due, expire maker orders, send the next maker quotes."""
        self.advance(now)
        for o in [o for o in self.resting if o["expires"] < now]:
            self.resting.remove(o)
            self._release(o["strategy"], o["notional"])
            if not any(x["strategy"] == o["strategy"] and x["symbol"] == o["symbol"] for x in self.resting):
                self.busy.discard((o["strategy"], o["symbol"]))
        order = list(self.books)
        self.rng.shuffle(order)
        for sym in order:
            b = self.books[sym]
            if not b.ok or b.spread_bp > MAX_SPREAD_BP or b.ask - b.bid < self.rules.mm_min_ticks * 0.01 - 1e-9 \
                    or now - self.last_mm[sym] < pd.Timedelta(seconds=self.rules.mm_every_s):
                continue
            self.last_mm[sym] = now
            imb = b.imbalance
            for strategy in ("market_maker", "maker_with_signal"):
                if (strategy, sym) in self.busy:
                    continue
                sides = [("buy", b.bid), ("sell", b.ask)]
                if strategy == "maker_with_signal":
                    sides = [x for x in sides if (x[0] == "buy" and imb > 0) or (x[0] == "sell" and imb < 0)]
                for side, px in sides:
                    size = self._reserve(strategy)
                    if size is None:
                        continue
                    delay = self._delay()
                    self.busy.add((strategy, sym))
                    self.resting.append({"strategy": strategy, "symbol": sym, "side": side, "price": px,
                                         "notional": size, "decision_time": now, "live_at": now + delay,
                                         "expires": now + delay + pd.Timedelta(seconds=self.rules.mm_wait_s),
                                         "spread_bp": b.spread_bp, "imbalance": imb,
                                         "latency_ms": delay.total_seconds() * 1e3})

    def take_closed(self) -> pd.DataFrame:
        out, self.closed = self.closed, []
        return pd.DataFrame(out, columns=COLUMNS)


# -----------------------------------------------------------------------------
# Google Sheet (optional): the trade log every few seconds
# -----------------------------------------------------------------------------
HEADER = ["Strategy", "Symbol", "Side", "Entry time (NY)", "Entry price", "Exit time (NY)", "Exit price",
          "Position $", "P&L $", "P&L mid $", "P&L bp", "P&L mid bp", "Spread bp", "Imbalance", "Latency ms",
          "Exit by"]


class SheetWriter:
    """Appends trades to the 'HFT trades' tab and rewrites its book line and summary, through a
    service account. Trades from row 6 (header in row 5), book line in A4, summary from R4."""

    TAB = "HFT trades"

    def __init__(self, sheet_id: str, creds_json: str):
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
        self.s = AuthorizedSession(creds)
        self.base = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"

    def _get(self, rng: str) -> list[list]:
        r = self.s.get(f"{self.base}/values/{rng}", timeout=30)
        r.raise_for_status()
        return r.json().get("values", [])

    def todays_trades(self, today: str) -> pd.DataFrame:
        """Make sure the tab has the current layout (an old layout is cleared once) and return today's
        trades already in it, so the book's equity carries over between runs."""
        if self._get(f"'{self.TAB}'!A5:P5") != [HEADER]:
            r = self.s.post(f"{self.base}/values:batchClear", json={"ranges": [f"'{self.TAB}'!A4:Z100000"]}, timeout=30)
            r.raise_for_status()
            r = self.s.put(f"{self.base}/values/'{self.TAB}'!A5:P5", params={"valueInputOption": "RAW"},
                           json={"values": [HEADER]}, timeout=30)
            r.raise_for_status()
            return pd.DataFrame(columns=COLUMNS)
        every = self._get(f"'{self.TAB}'!A6:P1000000")
        rows = [r for r in every if len(r) >= 12 and str(r[3]).startswith(today)]
        if len(rows) < len(every):                     # earlier days (archived, encrypted, on the results branch)
            r = self.s.post(f"{self.base}/values:batchClear", json={"ranges": [f"'{self.TAB}'!A6:P1000000"]}, timeout=60)
            r.raise_for_status()
            if rows:
                self.append_rows(rows)
        if not rows:
            return pd.DataFrame(columns=COLUMNS)
        n = len(HEADER)
        df = pd.DataFrame([r[:n] + [""] * (n - len(r[:n])) for r in rows], columns=HEADER)
        num = lambda c: pd.to_numeric(df[c], errors="coerce")
        return pd.DataFrame({"strategy": df["Strategy"], "symbol": df["Symbol"], "side": df["Side"],
                             "notional": num("Position $"), "pnl_usd": num("P&L $"), "pnl_mid_usd": num("P&L mid $"),
                             "pnl_bp": num("P&L bp"), "pnl_mid_bp": num("P&L mid bp"), "spread_bp": num("Spread bp"),
                             "imbalance": num("Imbalance"), "latency_ms": num("Latency ms")})

    @staticmethod
    def _rows(trades: pd.DataFrame) -> list[list]:
        def ny(ts):
            return pd.Timestamp(ts).tz_convert(NY).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return [[r.strategy, r.symbol, r.side, ny(r.entry_time), round(float(r.entry_price), 4), ny(r.exit_time),
                 round(float(r.exit_price), 4), round(float(r.notional), 2), round(float(r.pnl_usd), 4),
                 round(float(r.pnl_mid_usd), 4), round(float(r.pnl_bp), 3), round(float(r.pnl_mid_bp), 3),
                 round(float(r.spread_bp), 3), round(float(r.imbalance), 3), round(float(r.latency_ms), 2), r.exit_by]
                for r in trades.itertuples()]

    def append(self, trades: pd.DataFrame) -> None:
        if not trades.empty:
            self.append_rows(self._rows(trades))

    def append_rows(self, rows: list[list]) -> None:
        r = self.s.post(f"{self.base}/values/'{self.TAB}'!A6:P:append",
                        params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                        json={"values": rows}, timeout=60)
        r.raise_for_status()

    def status(self, text: str, book_line: str, summary_rows: list[list]) -> None:
        data = [{"range": f"'{self.TAB}'!A3", "values": [[text]]},
                {"range": f"'{self.TAB}'!A4", "values": [[book_line]]},
                {"range": f"'{self.TAB}'!R4:Z{4 + len(summary_rows)}", "values": summary_rows}]
        r = self.s.post(f"{self.base}/values:batchUpdate", json={"valueInputOption": "RAW", "data": data}, timeout=30)
        r.raise_for_status()


def summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    g = trades.groupby("strategy")
    return pd.DataFrame({"trades": g.size(), "pnl_usd": g["pnl_usd"].sum(), "pnl_mid_usd": g["pnl_mid_usd"].sum(),
                         "avg_pnl_bp": g["pnl_bp"].mean(), "avg_pnl_mid_bp": g["pnl_mid_bp"].mean(),
                         "avg_spread_bp": g["spread_bp"].mean(),
                         "hit_rate": g["pnl_bp"].apply(lambda x: (x > 0).mean()),
                         "avg_latency_ms": g["latency_ms"].mean()}).reset_index()


def _summary_rows(all_trades: pd.DataFrame) -> list[list]:
    head = [["Strategy", "Trades", "Net P&L $", "Net P&L mid $", "Avg P&L bp", "Avg P&L mid bp", "Avg spread bp",
             "Hit rate", "Avg latency ms"]]
    s = summary(all_trades)
    rows = [[r.strategy, int(r.trades), round(r.pnl_usd, 2), round(r.pnl_mid_usd, 2), round(r.avg_pnl_bp, 3),
             round(r.avg_pnl_mid_bp, 3), round(r.avg_spread_bp, 3), round(r.hit_rate, 3), round(r.avg_latency_ms, 2)]
            for r in s.itertuples()]
    if len(all_trades):
        t = all_trades
        rows.append(["TOTAL", int(len(t)), round(t["pnl_usd"].sum(), 2), round(t["pnl_mid_usd"].sum(), 2),
                     round(t["pnl_bp"].mean(), 3), round(t["pnl_mid_bp"].mean(), 3), round(t["spread_bp"].mean(), 3),
                     round((t["pnl_bp"] > 0).mean(), 3), round(t["latency_ms"].mean(), 2)])
    return head + rows


TRACKER_USD = 10_000.0          # the $0 tracker's hypothetical book when no strategy passed the replay


def book_line(all_trades: pd.DataFrame, equity: dict[str, float], book_usd: float = BOOK_USD,
              label: str = "HFT sleeve") -> str:
    net = float(all_trades["pnl_usd"].sum()) if len(all_trades) else 0.0
    eq = sum(equity.values())
    parts = ", ".join(f"{k} ${v:,.2f}" for k, v in equity.items()) or "none (no strategy passed the replay test)"
    pct = 100 * net / book_usd if book_usd else 0.0
    return (f"{label}: ${book_usd:,.0f} at the open -> equity ${eq:,.2f} (net P&L ${net:+,.2f}, {pct:+.3f}%). "
            f"By strategy: {parts}. Each position = 1/{SLOTS} of its strategy's equity.")


def previous_vix() -> float | None:
    """Yesterday's VIX close (imbalance_flip fades the book above 20)."""
    try:
        import yfinance as yf

        v = yf.download("^VIX", period="10d", progress=False, auto_adjust=False)["Close"].squeeze().dropna()
        today = pd.Timestamp.now(tz=NY).normalize().tz_localize(None)
        v = v[pd.to_datetime(v.index).tz_localize(None) < today]
        return float(v.iloc[-1]) if len(v) else None
    except Exception as exc:
        LOG.warning("VIX unavailable (%s)", exc)
        return None


def _pull(client, url: str, key: str, symbols: list[str], start: pd.Timestamp, end: pd.Timestamp,
          group: int = 200) -> dict:
    """Every quote / trade of ``symbols`` between ``start`` and ``end``, in groups of 200 symbols."""
    out: dict[str, list] = defaultdict(list)
    for i in range(0, len(symbols), group):
        params = {"symbols": ",".join(to_alpaca(s) for s in symbols[i:i + group]), "start": start.isoformat(),
                  "end": end.isoformat(), "limit": 10000, "feed": "iex", "sort": "asc"}
        for _ in range(30):
            data = client._get(params, url)
            for sym, rows in (data.get(key) or {}).items():
                out[sym] += rows
            token = data.get("next_page_token")
            if not token:
                break
            params["page_token"] = token
    return out


def universe_symbols(n: int) -> list[str]:
    """The ``n`` largest US stocks (the momentum flip sleeve's universe), the core symbols first."""
    if n <= len(SYMBOLS):
        return SYMBOLS[:n]
    try:
        from .flip_sleeve import universe

        names = [t.replace(".", "-") for t in universe()]
    except Exception as exc:
        LOG.warning("universe unavailable (%s) - core symbols only", exc)
        return list(SYMBOLS)
    return list(dict.fromkeys(SYMBOLS + names))[:n]


def run(minutes: float, out_dir: str | Path = "logs/hft", symbols: list[str] | None = None,
        poll_s: float = 1.0, sheet_every_s: float = 5.0) -> Path | None:
    """Trade in the shadow until ``minutes`` have passed or the market closes; returns the trade log."""
    from ..data.intraday import AlpacaBars

    symbols = symbols or SYMBOLS
    allowed = set(symbols)
    client = AlpacaBars(feed="iex", per_minute=140)     # leaves headroom for other data calls
    sheet, earlier = None, pd.DataFrame(columns=COLUMNS)
    if os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") and os.environ.get("HFT_SHEET_ID"):
        try:
            sheet = SheetWriter(os.environ["HFT_SHEET_ID"], os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
            earlier = sheet.todays_trades(pd.Timestamp.now(tz=NY).strftime("%Y-%m-%d"))
            LOG.info("shadow HFT: writing to the Google Sheet every %.0f s (%d earlier trades today)",
                     sheet_every_s, len(earlier))
        except Exception as exc:
            LOG.warning("Google Sheet unavailable (%s) - log file only", exc.__class__.__name__)
    rules = load_rules()
    book_usd = book_split().get("hft", BOOK_USD)
    vix = previous_vix() if "imbalance_flip" in rules else None
    equity = {k: book_usd / len(rules) for k in rules} if rules else {}
    if len(earlier):                                   # carry the day's realised P&L into this run
        for k, v in earlier.groupby("strategy")["pnl_usd"].sum().items():
            if k in equity:
                equity[k] += float(v)
    LOG.info("shadow HFT: strategies %s, VIX %s", list(rules), vix)
    tracker = not rules
    if tracker:                                        # nothing passed the replay test: keep trading the replay's
        rules = load_rules(include_disabled=True)      # picks live, as a $0 tracker on a hypothetical book
        book_usd = TRACKER_USD
        vix = previous_vix() if "imbalance_flip" in rules else None
        equity = {k: book_usd / len(rules) for k in rules}
        if len(earlier):
            for k, v in earlier.groupby("strategy")["pnl_usd"].sum().items():
                if k in equity:
                    equity[k] += float(v)
        LOG.info("shadow HFT: tracker mode ($0 allocated) with %s", list(rules))
    label = "TRACKER ($0 allocated, NOT part of the $10,000 book) - hypothetical book" if tracker else "HFT sleeve"
    sims = {k: ShadowHFT(symbols, seed=int(time.time()) + i, equity={k: equity[k]}, rules=r, vix=vix)
            for i, (k, r) in enumerate(rules.items())}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"hft_trades_{pd.Timestamp.now(tz=NY):%Y%m%d_%H%M}.csv"
    stop = time.time() + minutes * 60
    last = pd.Timestamp.now(tz="UTC") - pd.Timedelta(seconds=5)
    unsent, everything = [], ([earlier] if len(earlier) else [])
    last_sheet = 0.0
    while time.time() < stop:
        now_ny = pd.Timestamp.now(tz=NY)
        hm = now_ny.hour * 60 + now_ny.minute
        if now_ny.weekday() >= 5 or hm >= 16 * 60:
            break
        if hm < 9 * 60 + 31:                            # skip the opening auction's aftermath
            time.sleep(10)
            last = pd.Timestamp.now(tz="UTC") - pd.Timedelta(seconds=5)
            continue
        now = pd.Timestamp.now(tz="UTC")
        try:
            quotes = _pull(client, QUOTES_URL, "quotes", symbols, last, now)
            trades = _pull(client, TRADES_URL, "trades", symbols, last, now)
        except Exception as exc:
            LOG.warning("shadow HFT poll failed: %s", exc)
            time.sleep(poll_s)
            continue
        events = []
        for sym, rows in quotes.items():
            events += [(pd.Timestamp(q["t"]), 0, sym, q) for q in rows]
        for sym, rows in trades.items():
            events += [(pd.Timestamp(r["t"]), 1, sym, r) for r in rows]
        for t, kind, sym, r in sorted(events, key=lambda e: (e[0], e[1])):
            sym = sym.replace(".", "-")
            if sym not in allowed:
                continue
            for hft in sims.values():
                if kind == 0:
                    hft.on_quote(sym, t, r.get("bp", 0), r.get("bs", 0), r.get("ap", 0), r.get("as", 0))
                else:
                    hft.on_trade(sym, t, r.get("p", 0), r.get("s", 0))
        for hft in sims.values():
            hft.step(now)
        done = pd.concat([h.take_closed() for h in sims.values()] or [pd.DataFrame(columns=COLUMNS)],
                         ignore_index=True)
        if len(done):
            done.to_csv(path, mode="a", header=not path.exists(), index=False)
            unsent.append(done)
            everything.append(done)
        if sheet is not None and time.time() - last_sheet >= sheet_every_s:
            last_sheet = time.time()
            try:
                new = pd.concat(unsent, ignore_index=True) if unsent else pd.DataFrame(columns=COLUMNS)
                sheet.append(new)
                unsent = []
                total = pd.concat(everything, ignore_index=True) if everything else pd.DataFrame(columns=COLUMNS)
                sheet.status(f"Live{' TRACKER ($0 allocated)' if tracker else ''} - last update "
                             f"{pd.Timestamp.now(tz=NY):%Y-%m-%d %H:%M:%S} New York - "
                             f"{len(total)} trades today", book_line(total, {k: h.equity[k] for k, h in sims.items()}, book_usd, label),
                             _summary_rows(total))
            except Exception as exc:
                LOG.warning("Google Sheet update failed: %s", exc)
        last = now
        time.sleep(max(0.0, poll_s - (pd.Timestamp.now(tz="UTC") - now).total_seconds()))
    n = sum(len(d) for d in everything) - len(earlier)
    LOG.info("shadow HFT: %d simulated trades logged to %s", n, path)
    return path if path.exists() else None


def main(argv=None):
    import argparse

    from ..utils import setup_logging

    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=330)
    ap.add_argument("--out", default="logs/hft")
    ap.add_argument("--universe", type=int, default=1000, help="trade the N largest US stocks")
    args = ap.parse_args(argv)
    setup_logging()
    p = run(args.minutes, args.out, symbols=universe_symbols(args.universe))
    if p is not None:
        print(summary(pd.read_csv(p)).to_string(index=False))


if __name__ == "__main__":
    main()
