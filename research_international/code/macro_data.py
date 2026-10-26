"""Rates and FX for the international work, from FRED and Yahoo.

* OECD long-term (10y government) and 3-month interbank rates per country,
  monthly, from FRED (IRLTLT01xxM156N, IR3TIB01xxM156N). A monthly value is
  the month's average and is published after the month ends, so each value is
  only used from the 15th of the following month (no lookahead).
* US 10y and 2y Treasury yields, daily (DGS10, DGS2), used with a 1-day lag.
* USD crosses for every currency in the universes, daily, from Yahoo.

Output: one daily parquet, columns `lt:<cc>`, `st:<cc>`, `us10y`, `us2y`,
`fx:<ccy>` (local currency per USD).

    python research_international/code/macro_data.py --out data2/macro.parquet
"""
from __future__ import annotations

import argparse
import io
import time
import warnings

import pandas as pd
import requests
import yfinance as yf

warnings.filterwarnings("ignore")

OECD = {"JP": "Japan", "KR": "Korea", "AU": "Australia", "NZ": "New Zealand", "IN": "India", "ID": "Indonesia",
        "CN": "China", "GB": "UK", "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain", "NL": "Netherlands",
        "SE": "Sweden", "CH": "Switzerland", "CA": "Canada", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
        "BE": "Belgium", "AT": "Austria", "PT": "Portugal", "GR": "Greece", "PL": "Poland", "IL": "Israel",
        "MX": "Mexico", "CL": "Chile", "ZA": "South Africa", "BR": "Brazil", "TR": "Turkey"}
ALT = {"lt": {"IN": "INDIRLTLT01STM", "CN": "CHNIRLTLT01STM", "BR": "BRAIRLTLT01STM", "TR": "TURIRLTLT01STM", "ID": "IDNIRLTLT01STM"}}
FX = ["JPY", "KRW", "TWD", "HKD", "CNY", "INR", "IDR", "SGD", "MYR", "THB", "AUD", "NZD", "GBP", "EUR", "CHF", "SEK",
      "CAD", "NOK", "DKK", "PLN", "ILS", "MXN", "CLP", "ZAR", "BRL", "TRY", "SAR", "KWD", "QAR", "PKR", "VND"]


def fred(series_id: str) -> pd.Series | None:
    for attempt in range(3):
        try:
            r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}", timeout=60)
            if r.status_code != 200:
                return None
            df = pd.read_csv(io.StringIO(r.text))
            s = pd.to_numeric(df.iloc[:, 1], errors="coerce")
            s.index = pd.to_datetime(df.iloc[:, 0])
            return s.dropna().rename(series_id)
        except Exception:  # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return None


def monthly_to_daily(s: pd.Series, days: pd.DatetimeIndex) -> pd.Series:
    """Month-average value dated the 1st of month m becomes usable on the 15th of month m+1."""
    avail = s.copy()
    avail.index = s.index + pd.offsets.MonthBegin(1) + pd.Timedelta(days=14)
    return avail.reindex(days.union(avail.index)).ffill().reindex(days)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data2/macro.parquet")
    args = ap.parse_args(argv)
    days = pd.bdate_range("2000-01-01", pd.Timestamp.today().normalize())
    cols, got = {}, []
    for cc in OECD:
        for kind, sid in (("lt", f"IRLTLT01{cc}M156N"), ("st", f"IR3TIB01{cc}M156N")):
            s = fred(sid)
            if (s is None or len(s) <= 24) and cc in ALT.get(kind, {}):
                s = fred(ALT[kind][cc])
            if s is not None and len(s) > 24:
                cols[f"{kind}:{cc}"] = monthly_to_daily(s, days)
                got.append(f"{kind}:{cc} from {s.index[0].year}")
    for name, sid in (("us10y", "DGS10"), ("us2y", "DGS2")):
        s = fred(sid)
        if s is not None:
            cols[name] = s.reindex(days.union(s.index)).ffill().reindex(days).shift(1)
    fx = yf.download([f"{c}=X" for c in FX], start="2000-01-01", progress=False, auto_adjust=False)["Close"]
    fx.index = pd.to_datetime(fx.index).tz_localize(None)
    for c in FX:
        if f"{c}=X" in fx:
            cols[f"fx:{c}"] = fx[f"{c}=X"].reindex(days).ffill()
    out = pd.DataFrame(cols, index=days)
    out.to_parquet(args.out)
    print(f"{out.shape[1]} columns; rates: {', '.join(got)}")
    print("missing FX:", [c for c in FX if f"fx:{c}" not in out or out[f'fx:{c}'].notna().sum() < 500])


if __name__ == "__main__":
    main()
