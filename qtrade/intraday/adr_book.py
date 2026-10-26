"""The ADR book: US-listed Asian shares traded against their home markets.

Tokyo, Seoul, Hong Kong, Taipei, Mumbai and Sydney close before New York
opens. On a US day D, an ADR's home listing has already traded its session D,
while the ADR last printed at the US close of D-1. The research
(``qtrade.research.asia``) found that the ADR's opening gap under-reacts to that
home move:

    residual = home close-to-close (session D, local currency)
               - the local currency's move against the dollar (up to day D-1)
               - the ADR's move from its D-1 close to the reference price

and the ADR keeps moving in the residual's direction until the US close. The
book goes long ADRs with a positive residual and short the negative ones,
equal weight, and closes everything at the close.

Execution matters: the backtest used the official opening price as the
reference, which is not known when market-on-open orders must be sent (Alpaca:
before 9:28). Two executable versions:

* ``premarket``: the reference is the last pre-market trade before 9:25 (free IEX
  feed); orders go in as market-on-open (no spread) and out market-on-close;
* ``after_open``: the reference is the official open; orders go in at ~9:35 as
  regular market orders (paying the spread) and out market-on-close.

``qtrade.research.asia.adr_executable`` measures both on 2016-2026 Alpaca bars.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils import LOG

NY = "America/New_York"

# ADR -> (home listing, FX ticker quoted as local currency per USD ("1/x" = USD per local), market)
ADRS = {
    # China (Hong Kong listings)
    "BABA": ("9988.HK", "HKD=X", "China"), "JD": ("9618.HK", "HKD=X", "China"),
    "BIDU": ("9888.HK", "HKD=X", "China"), "NTES": ("9999.HK", "HKD=X", "China"),
    "TCOM": ("9961.HK", "HKD=X", "China"), "BILI": ("9626.HK", "HKD=X", "China"),
    "LI": ("2015.HK", "HKD=X", "China"), "NIO": ("9866.HK", "HKD=X", "China"),
    "XPEV": ("9868.HK", "HKD=X", "China"), "YUMC": ("9987.HK", "HKD=X", "China"),
    "ZTO": ("2057.HK", "HKD=X", "China"), "TME": ("1698.HK", "HKD=X", "China"),
    "BEKE": ("2423.HK", "HKD=X", "China"), "HTHT": ("1179.HK", "HKD=X", "China"),
    "WB": ("9898.HK", "HKD=X", "China"), "BZ": ("2076.HK", "HKD=X", "China"),
    # Japan
    "SONY": ("6758.T", "JPY=X", "Japan"), "TM": ("7203.T", "JPY=X", "Japan"),
    "HMC": ("7267.T", "JPY=X", "Japan"), "MUFG": ("8306.T", "JPY=X", "Japan"),
    "SMFG": ("8316.T", "JPY=X", "Japan"), "MFG": ("8411.T", "JPY=X", "Japan"),
    "NMR": ("8604.T", "JPY=X", "Japan"), "TAK": ("4502.T", "JPY=X", "Japan"),
    "IX": ("8591.T", "JPY=X", "Japan"), "CAJ": ("7751.T", "JPY=X", "Japan"),
    # Korea
    "KB": ("105560.KS", "KRW=X", "Korea"), "SHG": ("055550.KS", "KRW=X", "Korea"),
    "PKX": ("005490.KS", "KRW=X", "Korea"), "LPL": ("034220.KS", "KRW=X", "Korea"),
    "KEP": ("015760.KS", "KRW=X", "Korea"), "SKM": ("017670.KS", "KRW=X", "Korea"),
    "KT": ("030200.KS", "KRW=X", "Korea"), "WF": ("316140.KS", "KRW=X", "Korea"),
    # India
    "IBN": ("ICICIBANK.NS", "INR=X", "India"), "HDB": ("HDFCBANK.NS", "INR=X", "India"),
    "INFY": ("INFY.NS", "INR=X", "India"), "WIT": ("WIPRO.NS", "INR=X", "India"),
    "RDY": ("DRREDDY.NS", "INR=X", "India"), "TTM": ("TATAMOTORS.NS", "INR=X", "India"),
    # Taiwan, Australia
    "TSM": ("2330.TW", "TWD=X", "Taiwan"), "UMC": ("2303.TW", "TWD=X", "Taiwan"),
    "ASX": ("3711.TW", "TWD=X", "Taiwan"), "CHT": ("2412.TW", "TWD=X", "Taiwan"),
    "BHP": ("BHP.AX", "1/AUDUSD=X", "Australia"),
}


def fx_log_return(series: pd.Series, ticker: str) -> pd.Series:
    """Daily log change of local currency per USD, whichever way Yahoo quotes the pair."""
    r = np.log(series.dropna()).diff()
    return -r if ticker.startswith("1/") else r


def residual(home_ret: float, fx_ret_prev: float, adr_prev_close: float, adr_ref: float) -> float:
    """Home move in dollars (FX lagged a day) minus the ADR's move to the reference price."""
    if not (np.isfinite(home_ret) and np.isfinite(adr_prev_close) and np.isfinite(adr_ref)) or adr_prev_close <= 0 \
            or adr_ref <= 0:
        return np.nan
    fx = fx_ret_prev if np.isfinite(fx_ret_prev) else 0.0
    return float(home_ret - fx - np.log(adr_ref / adr_prev_close))


def book_weights(resid: dict[str, float], gross: float, sign: float = 1.0, min_abs: float = 0.0,
                 shortable: set | None = None, markets: list[str] | None = None) -> dict[str, float]:
    """Equal-weight long / short by the residual's sign; ``gross`` = sum of |weights|."""
    picks = {t: np.sign(r) * sign for t, r in resid.items()
             if np.isfinite(r) and abs(r) > min_abs and (markets is None or ADRS.get(t, ("", "", ""))[2] in markets)}
    if shortable is not None:
        picks = {t: s for t, s in picks.items() if s > 0 or t in shortable}
    picks = {t: s for t, s in picks.items() if s != 0}
    if not picks:
        return {}
    w = gross / len(picks)
    return {t: float(s * w) for t, s in picks.items()}


# -----------------------------------------------------------------------------
# live inputs
# -----------------------------------------------------------------------------
def home_moves(today: pd.Timestamp, tickers: list[str] | None = None) -> pd.DataFrame:
    """Per ADR: today's home close-to-close (log, local) and yesterday's FX move, from Yahoo.
    Only rows whose home session is dated today (the home market traded today) are kept."""
    from ..data.loader import download_prices

    tickers = tickers or list(ADRS)
    homes = sorted({ADRS[t][0] for t in tickers})
    fxs = sorted({ADRS[t][1].removeprefix("1/") for t in tickers})
    md = download_prices(homes + fxs, start=(today - pd.Timedelta(days=15)).strftime("%Y-%m-%d"))
    rows = []
    day = pd.Timestamp(today).normalize().tz_localize(None)
    for t in tickers:
        home, fx, mkt = ADRS[t]
        if home not in md.close:
            continue
        c = md.close[home].dropna()
        if len(c) < 2 or c.index[-1].normalize() != day:
            continue                                       # the home market didn't trade today
        fxt = fx.removeprefix("1/")
        f = fx_log_return(md.close[fxt], fx) if fxt in md.close else pd.Series(dtype=float)
        f = f[f.index.normalize() < day]                   # FX up to yesterday only
        rows.append({"adr": t, "market": mkt, "home_ret": float(np.log(c.iloc[-1] / c.iloc[-2])),
                     "fx_ret_prev": float(f.iloc[-1]) if len(f) else np.nan})
    return pd.DataFrame(rows)


def build_targets(acfg, today: pd.Timestamp, prev_close: dict[str, float], ref_price: dict[str, float],
                  moves: pd.DataFrame, shortable: set | None, sign: float = 1.0) -> tuple[dict, pd.DataFrame]:
    """(weights, table of residuals) for today's ADR book."""
    rows = []
    for _, m in moves.iterrows():
        t = m["adr"]
        r = residual(m["home_ret"], m["fx_ret_prev"], prev_close.get(t, np.nan), ref_price.get(t, np.nan))
        rows.append({**m.to_dict(), "prev_close": prev_close.get(t), "ref_price": ref_price.get(t), "residual": r})
    tab = pd.DataFrame(rows)
    resid = dict(zip(tab["adr"], tab["residual"])) if len(tab) else {}
    w = book_weights(resid, acfg.adr_gross, sign, acfg.adr_min_residual, shortable, acfg.adr_markets)
    LOG.info("ADR book: %d ADRs with a home session today, %d priced, %d long / %d short", len(moves),
             int(np.isfinite(tab["residual"]).sum()) if len(tab) else 0, sum(v > 0 for v in w.values()),
             sum(v < 0 for v in w.values()))
    return w, tab
