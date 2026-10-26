"""Trade ledger for the Alpaca paper account: every fill, and every round trip with its P&L.

``python -m qtrade.live.ledger --out logs/ledger`` writes

* ``fills.csv``   - every fill since the account started (time, symbol, side, qty, price, order's
                    time in force: ``cls`` market-on-close, ``opg`` market-on-open, ``day`` market);
* ``trades.csv``  - round trips matched first-in first-out per symbol: opened / closed time, side,
                    shares, entry and exit price, P&L in dollars and percent, days held, how it was
                    entered and exited; positions still open are listed with their unrealised P&L;
* ``daily.csv``   - realised P&L per day.

Fill prices are market data from Alpaca, so the files are never published in the clear: with
``--public-key`` each file is encrypted (AES-256 with a random key, the key sealed with the RSA
public key) and only the holder of the private key can read them.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, setup_logging

PAPER = "https://paper-api.alpaca.markets/v2"
NY = "America/New_York"


def _session():
    import requests

    s = requests.Session()
    s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
                      "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    return s


def fetch_fills(s, base: str = PAPER) -> pd.DataFrame:
    rows, token = [], None
    while True:
        params = {"direction": "asc", "page_size": 100}
        if token:
            params["page_token"] = token
        r = s.get(f"{base}/account/activities/FILL", params=params, timeout=60)
        r.raise_for_status()
        page = r.json()
        rows += page
        if len(page) < 100:
            break
        token = page[-1]["id"]
    if not rows:
        return pd.DataFrame(columns=["time", "symbol", "side", "qty", "price", "order_id"])
    df = pd.DataFrame(rows)
    out = pd.DataFrame({"time": pd.to_datetime(df["transaction_time"], utc=True).dt.tz_convert(NY),
                        "symbol": df["symbol"], "side": df["side"].replace({"sell_short": "sell"}),
                        "qty": df["qty"].astype(float), "price": df["price"].astype(float),
                        "order_id": df["order_id"]})
    return out.sort_values("time").reset_index(drop=True)


def fetch_order_tif(s, order_ids: set[str], base: str = PAPER) -> dict[str, str]:
    """order id -> time in force, from the closed-orders list (paged by submission time)."""
    tif, after = {}, "2020-01-01T00:00:00Z"
    for _ in range(200):
        r = s.get(f"{base}/orders", params={"status": "all", "after": after, "limit": 500, "direction": "asc"},
                  timeout=60)
        r.raise_for_status()
        page = r.json()
        for o in page:
            tif[o["id"]] = o.get("time_in_force")
        if len(page) < 500:
            break
        after = page[-1]["submitted_at"]
    return {k: v for k, v in tif.items() if k in order_ids}


def round_trips(fills: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, deque]]:
    """FIFO-match fills per symbol. Returns (closed trades, open lots per symbol)."""
    lots: dict[str, deque] = defaultdict(deque)          # each lot: [signed qty, price, time, tif]
    trades = []
    for f in fills.itertuples(index=False):
        q = f.qty if f.side == "buy" else -f.qty
        tif = getattr(f, "tif", None)
        book = lots[f.symbol]
        while q != 0 and book and np.sign(book[0][0]) != np.sign(q):
            lot = book[0]
            m = min(abs(q), abs(lot[0]))
            direction = np.sign(lot[0])                    # +1 a long being sold, -1 a short being bought back
            pnl = direction * m * (f.price - lot[1])
            trades.append({"symbol": f.symbol, "side": "long" if direction > 0 else "short", "shares": m,
                           "opened": lot[2], "closed": f.time, "entry_price": lot[1], "exit_price": f.price,
                           "pnl": pnl, "return_pct": 100 * direction * (f.price / lot[1] - 1),
                           "days_held": (f.time - lot[2]).total_seconds() / 86400,
                           "entry_order": lot[3], "exit_order": tif})
            lot[0] -= direction * m
            q += direction * m
            if lot[0] == 0:
                book.popleft()
        if q != 0:
            book.append([q, f.price, f.time, tif])
    return pd.DataFrame(trades), lots


def merge_pieces(trades: pd.DataFrame) -> pd.DataFrame:
    """Partial fills split one position into several lots; merge lots opened the same day and closed by the
    same order (same minute) back into one trade, with share-weighted prices."""
    if trades.empty:
        return trades
    t = trades.copy()
    t["_open_day"] = pd.to_datetime(t["opened"]).dt.date
    t["_close_key"] = pd.to_datetime(t["closed"]).dt.floor("min")
    keys = ["symbol", "side", "_open_day", "_close_key", "entry_order", "exit_order"]
    rows = []
    for _, g in t.groupby(keys, dropna=False, sort=False):
        sh = g["shares"].sum()
        entry = float((g["entry_price"] * g["shares"]).sum() / sh)
        exit_ = float((g["exit_price"] * g["shares"]).sum() / sh)
        d = 1.0 if g["side"].iloc[0] == "long" else -1.0
        rows.append({**g.iloc[0][["symbol", "side", "entry_order", "exit_order"]].to_dict(),
                     "shares": sh, "opened": g["opened"].min(), "closed": g["closed"].max(),
                     "entry_price": entry, "exit_price": exit_, "pnl": float(g["pnl"].sum()),
                     "return_pct": 100 * d * (exit_ / entry - 1), "days_held": g["days_held"].max()})
    return pd.DataFrame(rows)


def open_positions(lots: dict[str, deque], marks: dict[str, float]) -> pd.DataFrame:
    rows = []
    for sym, book in lots.items():
        for q, px, t, tif in book:
            mark = marks.get(sym, np.nan)
            d = np.sign(q)
            rows.append({"symbol": sym, "side": "long" if d > 0 else "short", "shares": abs(q), "opened": t,
                         "closed": pd.NaT, "entry_price": px, "exit_price": mark,
                         "pnl": d * abs(q) * (mark - px), "return_pct": 100 * d * (mark / px - 1),
                         "days_held": np.nan, "entry_order": tif, "exit_order": "still open (marked)"})
    return pd.DataFrame(rows)


def encrypt(path: Path, public_key: str) -> list[Path]:
    """path -> path.enc (AES-256-CBC, PBKDF2) + path.key.enc (the random passphrase, RSA-OAEP sealed)."""
    key = os.urandom(32).hex()
    keyfile = path.with_suffix(path.suffix + ".key")
    keyfile.write_text(key)
    enc, kenc = path.with_suffix(path.suffix + ".enc"), path.with_suffix(path.suffix + ".key.enc")
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-in", str(path), "-out", str(enc),
                    "-pass", f"file:{keyfile}"], check=True)
    subprocess.run(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", public_key, "-pkeyopt",
                    "rsa_padding_mode:oaep", "-in", str(keyfile), "-out", str(kenc)], check=True)
    keyfile.unlink()
    path.unlink()
    return [enc, kenc]


def decrypt(enc: Path, private_key: str) -> Path:
    kenc = Path(str(enc)[:-4] + ".key.enc")
    keyfile = Path(str(enc)[:-4] + ".key")
    subprocess.run(["openssl", "pkeyutl", "-decrypt", "-inkey", private_key, "-pkeyopt", "rsa_padding_mode:oaep",
                    "-in", str(kenc), "-out", str(keyfile)], check=True)
    out = Path(str(enc)[:-4])
    subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-in", str(enc), "-out", str(out),
                    "-pass", f"file:{keyfile}"], check=True)
    keyfile.unlink()
    return out


def build(out: Path, public_key: str | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    s = _session()
    fills = fetch_fills(s)
    tif = fetch_order_tif(s, set(fills["order_id"]))
    fills["tif"] = fills["order_id"].map(tif)
    trades, lots = round_trips(fills)
    r = s.get(f"{PAPER}/positions", timeout=60)
    r.raise_for_status()
    marks = {p["symbol"]: float(p["current_price"]) for p in r.json()}
    opened = open_positions(lots, marks)
    all_trades = merge_pieces(pd.concat([trades, opened], ignore_index=True))
    daily = trades.groupby(trades["closed"].dt.date)["pnl"].agg(["sum", "count"]).rename(
        columns={"sum": "realised_pnl", "count": "trades"}) if len(trades) else pd.DataFrame()
    files = {"fills.csv": fills.drop(columns=["order_id"]), "trades.csv": all_trades, "daily.csv": daily.reset_index()}
    written = []
    for name, df in files.items():
        p = out / name
        df.to_csv(p, index=False)
        written += encrypt(p, public_key) if public_key else [p]
    LOG.info("ledger: %d fills, %d closed trades (realised $%.2f), %d open lots", len(fills), len(trades),
             trades["pnl"].sum() if len(trades) else 0.0, len(opened))
    return {"fills": len(fills), "closed_trades": len(trades), "open_lots": len(opened), "files": [str(w) for w in written]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="logs/ledger")
    ap.add_argument("--public-key", default=None, help="encrypt every file to this RSA public key")
    args = ap.parse_args(argv)
    setup_logging()
    print(build(Path(args.out), args.public_key))


if __name__ == "__main__":
    main()
