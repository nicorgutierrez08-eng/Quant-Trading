"""Daily prices for the international universes, their indices and volatility gauges.

Per market, one parquet per field (open, high, low, close, adj_close, volume),
dates x tickers, in local currency. Open/high/low are dividend- and split-
adjusted with the same factor Yahoo applies to the close (adj_close / close),
so open-to-open returns are total returns. Also downloads:

* each market's benchmark index and any local volatility index Yahoo carries;
* the US-listed country ETFs (iShares MSCI etc.), for cross-country tests;
* the US VIX, the global stress gauge used by the strategy.

    python research_international/code/download.py --universe data/universe.csv --out data/prices
"""
from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

INDICES = {
    "Japan": "^N225", "Hong Kong": "^HSI", "Hong Kong (H-shares)": "^HSCE", "China": "000300.SS", "Korea": "^KS11",
    "Taiwan": "^TWII", "Singapore": "^STI", "Australia": "^AXJO", "India": "^NSEI", "Malaysia": "^KLSE",
    "Thailand": "^SET.BK", "New Zealand": "^NZ50", "UK": "^FTSE", "Germany": "^GDAXI", "France": "^FCHI",
    "Switzerland": "^SSMI", "Netherlands": "^AEX", "Spain": "^IBEX", "Italy": "FTSEMIB.MI", "Sweden": "^OMX",
    "Canada": "^GSPTSE",
    "Indonesia": "^JKSE", "Brazil": "^BVSP", "Mexico": "^MXX", "South Africa": "^J203.JO", "Turkey": "XU100.IS",
    "Saudi Arabia": "^TASI.SR", "Israel": "^TA125.TA", "Poland": "WIG20.WA", "Norway": "OSEBX.OL", "Denmark": "^OMXC25",
    "Finland": "^OMXH25", "Belgium": "^BFX", "Austria": "^ATX", "Portugal": "PSI20.LS", "Greece": "GD.AT",
    "Chile": "^IPSA", "Vietnam": "^VNINDEX.VN", "Pakistan": "^KSE",
}
VOL_INDICES = {"US": "^VIX", "India": "^INDIAVIX", "Japan": "^JNIV", "Europe": "^V2TX", "Hong Kong": "^VHSI",
               "Korea": "^VKOSPI", "Australia": "^AXVI"}
COUNTRY_ETFS = {
    "Japan": "EWJ", "Hong Kong": "EWH", "China": "FXI", "Korea": "EWY", "Taiwan": "EWT", "Singapore": "EWS",
    "Australia": "EWA", "India": "INDA", "Malaysia": "EWM", "Thailand": "THD", "New Zealand": "ENZL",
    "Indonesia": "EIDO", "Philippines": "EPHE", "UK": "EWU", "Germany": "EWG", "France": "EWQ", "Switzerland": "EWL",
    "Netherlands": "EWN", "Spain": "EWP", "Italy": "EWI", "Sweden": "EWD", "Canada": "EWC", "Brazil": "EWZ",
    "Mexico": "EWW", "South Africa": "EZA", "Turkey": "TUR", "Israel": "EIS", "Poland": "EPOL", "Norway": "NORW",
    "Denmark": "EDEN", "Finland": "EFNL", "Belgium": "EWK", "Austria": "EWO", "Portugal": "PGAL", "Greece": "GREK",
    "Chile": "ECH", "Saudi Arabia": "KSA", "Qatar": "QAT", "Kuwait": "KWT", "Vietnam": "VNM", "US": "SPY", "Asia ex-Japan": "AAXJ", "Emerging": "EEM", "EAFE": "EFA",
}
FIELDS = ("Open", "High", "Low", "Close", "Adj Close", "Volume")


def fetch(tickers: list[str], start: str, batch: int = 80, pause: float = 1.0) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    out = {f: [] for f in FIELDS}
    for i in range(0, len(tickers), batch):
        chunk = tickers[i:i + batch]
        for attempt in range(3):
            try:
                d = yf.download(chunk, start=start, auto_adjust=False, progress=False, threads=True, group_by="column")
                break
            except Exception as exc:  # noqa: BLE001 - network hiccups
                print(f"  retry {attempt + 1}: {exc}")
                time.sleep(5 * (attempt + 1))
        else:
            continue
        if d is None or d.empty:
            continue
        if not isinstance(d.columns, pd.MultiIndex):
            d.columns = pd.MultiIndex.from_product([d.columns, chunk[:1]])
        for f in FIELDS:
            if f in d.columns.get_level_values(0):
                out[f].append(d[f])
        time.sleep(pause)
    res = {}
    for f, parts in out.items():
        if parts:
            df = pd.concat(parts, axis=1)
            df = df.loc[:, ~df.columns.duplicated()]
            df.index = pd.to_datetime(df.index).tz_localize(None)
            res[f] = df.sort_index()
    return res


def save_market(fields: dict[str, pd.DataFrame], path: Path) -> dict:
    path.mkdir(parents=True, exist_ok=True)
    close, adj = fields["Close"], fields["Adj Close"]
    factor = (adj / close).where(close > 0)
    names = {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}
    for f, df in fields.items():
        if f in ("Open", "High", "Low"):
            df = df * factor.reindex_like(df)
        df.to_parquet(path / f"{names[f]}.parquet")
    have = close.notna().any()
    return {"tickers": int(have.sum()), "requested": int(close.shape[1]), "first": str(close.index[0].date()),
            "last": str(close.index[-1].date()), "rows": int(close.notna().sum().sum())}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--out", default="data/prices")
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--markets", default=None, help="comma-separated subset")
    args = ap.parse_args(argv)
    u = pd.read_csv(args.universe)
    out = Path(args.out)
    rows = []
    markets = args.markets.split(",") if args.markets else list(dict.fromkeys(u["market"]))
    for m in markets:
        tick = u.loc[u["market"] == m, "ticker"].dropna().astype(str).unique().tolist()
        t0 = time.time()
        f = fetch(tick, args.start)
        if "Close" not in f:
            print(f"{m}: nothing downloaded")
            continue
        info = save_market(f, out / m.replace(" ", "_").replace("(", "").replace(")", ""))
        rows.append({"market": m, **info})
        print(f"{m:22s} {info['tickers']}/{info['requested']} tickers, {info['first']} -> {info['last']} ({time.time() - t0:.0f}s)")
    extra = {**{f"idx:{k}": v for k, v in INDICES.items()}, **{f"vol:{k}": v for k, v in VOL_INDICES.items()},
             **{f"etf:{k}": v for k, v in COUNTRY_ETFS.items()}}
    f = fetch(list(extra.values()), args.start, batch=40)
    adj = f["Adj Close"].rename(columns={v: k for k, v in extra.items()})
    close = f["Close"].rename(columns={v: k for k, v in extra.items()})
    (out / "_series").mkdir(parents=True, exist_ok=True)
    adj.to_parquet(out / "_series" / "adj_close.parquet")
    close.to_parquet(out / "_series" / "close.parquet")
    got = adj.notna().any()
    print(f"index/vol/ETF series: {int(got.sum())}/{len(extra)} found; missing: {sorted(c for c in adj.columns if not got[c])}")
    pd.DataFrame(rows).to_csv(out / "coverage.csv", index=False)


if __name__ == "__main__":
    main()
