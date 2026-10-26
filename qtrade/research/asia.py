"""Asian markets: lead-lag with the US, ADRs vs their home listings, and the
overnight / reversal strategies inside each Asian market.

Asia trades while New York sleeps: Tokyo, Seoul and Sydney open around
00:00 UTC, Hong Kong, Shanghai and Taipei at 01:00-01:30, Mumbai at 03:45, and
all have closed before New York opens at 13:30-14:30 UTC. So an Asian session on
date D sits between the US sessions of D-1 and D. Three studies, daily data
(Yahoo), chosen on 2006-2014 and checked on 2015-2026 like everything else:

1. **Lead-lag** (indices): does the US day predict the next Asian session -
   the opening gap (descriptive: the open simply absorbs the news) and,
   tradable, the move *after* the Asian open (index futures / ETFs)? Does the
   Asian session predict the US day after the US open (SPY market-on-open in,
   market-on-close out, both auctions)?
2. **ADRs vs home shares** (TSMC, Sony, Toyota, Alibaba, Infosys, BHP ...): when
   the home listing has moved more (in dollars) than the ADR's opening gap,
   does the ADR keep moving during the US day? Tradable on Alpaca at the
   auctions. And does the ADR's US day predict the home listing's next session?
3. **Inside each Asian market** (30-40 large caps per market): the auction
   trader's overnight persistence, a daily version of the end-of-day fade, and
   1- / 5-day reversal, before and after each market's costs (commission and
   stamp / transaction taxes). IBKR offers Japan, Hong Kong and Australia;
   Korea, Taiwan and India are not open to it (signals only).

Caveats: the stock lists are today's large caps (survivorship flatters
long-only, matters less for long-short reversal books); Yahoo's opening prices
for some Asian indices and stocks are unreliable in early years (days with the
open exactly at the previous close are dropped); FX closes are London / New
York time, not the Asian close.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

P1 = ("2006-01-01", "2014-12-31")
P2 = ("2015-01-01", "2026-12-31")

INDICES = {"US": "SPY", "Japan": "^N225", "Hong Kong": "^HSI", "China": "000001.SS", "Korea": "^KS11",
           "Taiwan": "^TWII", "Australia": "^AXJO", "India": "^BSESN", "Singapore": "^STI"}

# index ETFs: their open is a traded price; an index's "open" mixes in stocks that haven't opened yet
# (the ASX opens in alphabetical groups from 10:00 to 10:10), which fakes predictability after the open
INDEX_ETFS = {"Japan": "1321.T", "Hong Kong": "2800.HK", "Australia": "STW.AX", "Korea": "069500.KS",
              "Taiwan": "0050.TW", "India": "NIFTYBEES.NS", "Singapore": "ES3.SI", "China": "510300.SS"}
# round trip for the ETFs (Hong Kong ETFs pay no stamp duty)
ETF_COST = {"Japan": 10.0, "Hong Kong": 11.0, "Australia": 16.0, "Korea": 5.0, "Taiwan": 13.0, "India": 25.0,
            "Singapore": 16.0, "China": 6.0}

# ADR / US listing -> (home listing, FX ticker quoted as local currency per USD, or "1/x" for USD per local)
from ..intraday.adr_book import ADRS as _ADR_BOOK

ADRS = {t: (h, f) for t, (h, f, _) in _ADR_BOOK.items()}
ADR_MARKET = {t: m for t, (_, _, m) in _ADR_BOOK.items()}

STOCKS = {
    "Japan": ["7203.T", "6758.T", "9984.T", "8306.T", "6861.T", "9432.T", "8035.T", "6098.T", "4063.T", "9983.T",
              "7974.T", "6501.T", "8058.T", "8001.T", "4502.T", "6367.T", "6902.T", "7267.T", "4568.T", "6954.T",
              "8316.T", "8766.T", "6594.T", "7741.T", "6981.T", "4519.T", "6273.T", "9433.T", "2914.T", "8031.T",
              "6702.T", "6752.T", "7011.T", "4661.T", "6146.T", "6857.T", "6920.T", "8411.T", "7751.T", "4901.T"],
    "Hong Kong": ["0700.HK", "0005.HK", "1299.HK", "0941.HK", "0939.HK", "1398.HK", "2318.HK", "0388.HK",
                  "0001.HK", "0016.HK", "0883.HK", "1810.HK", "2020.HK", "0027.HK", "1211.HK", "0011.HK",
                  "0002.HK", "0003.HK", "0006.HK", "0012.HK", "0066.HK", "0175.HK", "0267.HK", "0386.HK",
                  "0857.HK", "2388.HK", "1088.HK", "2628.HK", "3988.HK", "0688.HK", "1113.HK", "0823.HK",
                  "0981.HK", "2382.HK", "3690.HK", "9988.HK"],
    "Korea": ["005930.KS", "000660.KS", "035420.KS", "005380.KS", "051910.KS", "006400.KS", "035720.KS",
              "000270.KS", "068270.KS", "105560.KS", "055550.KS", "005490.KS", "012330.KS", "207940.KS",
              "028260.KS", "066570.KS", "003550.KS", "017670.KS", "034730.KS", "015760.KS", "032830.KS",
              "086790.KS", "009150.KS", "010950.KS", "018260.KS", "033780.KS", "011170.KS", "096770.KS"],
    "Taiwan": ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2412.TW", "2881.TW", "2882.TW", "2891.TW",
               "2303.TW", "3711.TW", "2886.TW", "1301.TW", "1303.TW", "2002.TW", "2357.TW", "3008.TW",
               "2884.TW", "2892.TW", "1216.TW", "2207.TW", "3034.TW", "2379.TW", "2395.TW", "3045.TW",
               "6505.TW", "2603.TW", "2885.TW", "5880.TW", "2880.TW"],
    "Australia": ["BHP.AX", "CBA.AX", "CSL.AX", "NAB.AX", "WBC.AX", "ANZ.AX", "WES.AX", "MQG.AX", "WOW.AX",
                  "FMG.AX", "RIO.AX", "TLS.AX", "WDS.AX", "GMG.AX", "TCL.AX", "ALL.AX", "COL.AX", "STO.AX",
                  "REA.AX", "SUN.AX", "QBE.AX", "IAG.AX", "AMC.AX", "BXB.AX", "ORG.AX", "S32.AX", "JHX.AX",
                  "COH.AX", "RMD.AX", "ASX.AX"],
    "India": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS",
              "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
              "BAJFINANCE.NS", "HCLTECH.NS", "SUNPHARMA.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS",
              "NESTLEIND.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "M&M.NS", "JSWSTEEL.NS",
              "TECHM.NS", "HINDALCO.NS", "CIPLA.NS"],
}

# round-trip cost in bp at the auctions (commission both sides + taxes / stamp), IBKR Pro where offered
COSTS = {
    "Japan": (10.0, True, "0.05% commission each side, no stamp duty"),
    "Hong Kong": (32.0, True, "0.05% commission + 0.1% stamp duty each side (0.13% Aug 2021-Nov 2023) + fees"),
    "Australia": (16.0, True, "0.08% commission each side, no stamp duty"),
    "Korea": (23.0, False, "securities transaction tax ~0.18-0.25% on sales + broker fees; not on IBKR"),
    "Taiwan": (33.0, False, "0.3% transaction tax on sales + broker fees; not on IBKR"),
    "India": (25.0, False, "0.1% STT each side + fees; not open to non-resident IBKR accounts"),
    "US": (0.0, True, "IBKR Lite / Alpaca: no commission; SEC + TAF fees under 0.3 bp"),
}


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 120 and x.std() > 0 else np.nan


def _corr_t(x: pd.Series, y: pd.Series) -> tuple[float, float, int]:
    ok = x.notna() & y.notna()
    n = int(ok.sum())
    if n < 120 or x[ok].std() == 0 or y[ok].std() == 0:
        return np.nan, np.nan, n
    c = float(np.corrcoef(x[ok], y[ok])[0, 1])
    return c, c * np.sqrt(n), n


def legs(md) -> dict[str, pd.DataFrame]:
    """Per-ticker session returns on each ticker's own trading days (log)."""
    o, c = md.open, md.close
    out = {}
    for t in c.columns:
        f = pd.DataFrame({"open": o[t], "close": c[t]}).dropna()
        f = f[(f["open"] > 0) & (f["close"] > 0)]
        prev = f["close"].shift(1)
        gap = np.log(f["open"] / prev)
        intra = np.log(f["close"] / f["open"])
        # Yahoo often prints the open at the previous close for Asian data (no real opening price)
        bad = (f["open"] == prev) | (f["open"] == f["close"])
        out[t] = pd.DataFrame({"gap": gap.mask(bad), "intraday": intra.mask(bad), "cc": np.log(f["close"] / prev),
                               "bad_open": bad})
    return out


def _align_after(src: pd.Series, target_days: pd.DatetimeIndex, strictly: bool) -> pd.Series:
    """For each target day D: the source's value on its last session before D (strictly earlier date)
    or on or before D."""
    s = src.dropna()
    pos = s.index.searchsorted(target_days, side="left" if strictly else "right") - 1
    vals = np.where(pos >= 0, s.to_numpy()[np.clip(pos, 0, None)], np.nan)
    stale = np.where(pos >= 0, (target_days - s.index[np.clip(pos, 0, None)]).days > 5, True)
    return pd.Series(np.where(stale, np.nan, vals), index=target_days)


def _strategy_rows(name: str, sig: pd.Series, ret: pd.Series, cost_bp: float) -> dict:
    """Trade sign(signal) on the target leg; direction fixed on 2006-2014."""
    ok = sig.notna() & ret.notna()
    s1 = (np.sign(sig) * ret)[ok][P1[0]:P1[1]]
    d = np.sign(s1.mean()) if len(s1) else 1.0
    pnl = (d * np.sign(sig) * ret)[ok]
    net = pnl - cost_bp / 1e4 * (np.sign(sig)[ok] != 0)
    return {"strategy": name, "direction": "+" if d > 0 else "-",
            "sharpe_2006_14": _sharpe(pnl[P1[0]:P1[1]]), "sharpe_2015_26": _sharpe(pnl[P2[0]:P2[1]]),
            "net_sharpe_2015_26": _sharpe(net[P2[0]:P2[1]]), "avg_bp_2015_26": float(pnl[P2[0]:P2[1]].mean() * 1e4),
            "cost_bp": cost_bp}


def lead_lag(L: dict[str, pd.DataFrame], instruments: dict | None = None, etf: bool = False
             ) -> tuple[pd.DataFrame, pd.DataFrame]:
    us = L.get(INDICES["US"])
    rows, strats = [], []
    if us is None:
        return pd.DataFrame(), pd.DataFrame()
    asia_cc = {}
    for mkt, tk in (instruments or INDICES).items():
        if mkt == "US" or tk not in L:
            continue
        a = L[tk]
        asia_cc[mkt] = a["cc"]
        tests = [
            ("US close-to-close (D-1)", "gap", _align_after(us["cc"], a.index, True), a["gap"], False),
            ("US close-to-close (D-1)", "after the open", _align_after(us["cc"], a.index, True), a["intraday"], True),
            ("US open-to-close (D-1)", "after the open", _align_after(us["intraday"], a.index, True), a["intraday"], True),
            (f"{mkt} close-to-close (D)", "US gap", _align_after(a["cc"], us.index, False), us["gap"], False),
            (f"{mkt} close-to-close (D)", "US after the open", _align_after(a["cc"], us.index, False),
             us["intraday"], True),
            (f"{mkt} open-to-close (D)", "US after the open", _align_after(a["intraday"], us.index, False),
             us["intraday"], True),
        ]
        for src, tgt, x, y, tradable in tests:
            target_mkt = "US" if tgt.startswith("US") else mkt
            row = {"market": mkt, "instrument": tk, "signal": src, "target": f"{target_mkt}: {tgt}",
                   "tradable": tradable}
            for tag, (a0, b0) in (("2006_14", P1), ("2015_26", P2)):
                row[f"corr_{tag}"], row[f"t_{tag}"], row[f"n_{tag}"] = _corr_t(x[a0:b0], y[a0:b0])
            rows.append(row)
            if tradable:
                # SPY auctions; Asian index futures (2 bp) or the ETF at its own costs
                cost = 0.0 if target_mkt == "US" else (ETF_COST.get(mkt, 20.0) if etf else 2.0)
                strats.append({"market": mkt, "instrument": tk,
                               **_strategy_rows(f"{src} -> {target_mkt} {tgt}", x, y, cost)})
    if asia_cc and not etf:
        comp = pd.DataFrame({m: _align_after(s, us.index, False) for m, s in asia_cc.items()}).mean(axis=1)
        for tgt, y in (("US gap", us["gap"]), ("US after the open", us["intraday"])):
            row = {"market": "Asia (average)", "signal": "Asian markets' average close-to-close (D)",
                   "target": tgt, "tradable": tgt != "US gap"}
            for tag, (a0, b0) in (("2006_14", P1), ("2015_26", P2)):
                row[f"corr_{tag}"], row[f"t_{tag}"], row[f"n_{tag}"] = _corr_t(comp[a0:b0], y[a0:b0])
            rows.append(row)
        strats.append({"market": "Asia (average)",
                       **_strategy_rows("Asia average (D) -> SPY open-to-close (D)", comp, us["intraday"], 0.0)})
    return pd.DataFrame(rows), pd.DataFrame(strats)


def _fx_ret(md, fx: str) -> pd.Series | None:
    inv = fx.startswith("1/")
    t = fx[2:] if inv else fx
    if t not in md.close:
        return None
    r = np.log(md.close[t].dropna()).diff()
    return -r if inv else r                      # log change of local currency per USD


ADR_VARIANTS = {
    # Yahoo dates an FX bar by its London / New York close, after the US open: using day D's FX move to
    # build day D's signal would peek at FX moves during the US session (which also move the ADR).
    "FX lagged a day (clean)": True,
    "no FX (home move in local currency)": None,
    "same-day FX (peeks: shown for comparison only)": False,
}


def _adr_book(p: pd.DataFrame, label: str) -> list[dict]:
    """Long / short ADRs by the sign of the residual, equal weight, market-on-open in, market-on-close out."""
    p = p.assign(pos=np.sign(p["resid"]))
    s1 = p[(p["date"] >= P1[0]) & (p["date"] <= P1[1])]
    d = np.sign((s1["pos"] * s1["ret"]).mean()) if len(s1) else 1.0
    if not np.isfinite(d) or d == 0:
        d = 1.0
    daily = (d * p["pos"] * p["ret"]).groupby(p["date"]).mean()
    n = p.groupby("date").size()
    rows = []
    for cost in (0.0, 1.0, 3.0):
        net = daily - cost / 1e4
        rows.append({"strategy": "ADRs: home-vs-gap residual, MOO in / MOC out", "variant": label,
                     "direction": "+" if d > 0 else "-", "cost_bp_round_trip": cost,
                     "sharpe_2006_14": _sharpe(net[P1[0]:P1[1]]), "sharpe_2015_26": _sharpe(net[P2[0]:P2[1]]),
                     "avg_bp_2015_26": float(daily[P2[0]:P2[1]].mean() * 1e4),
                     "adrs_per_day_2015_26": float(n[P2[0]:P2[1]].mean())})
    return rows


def adr_study(md, L: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, panels = [], {k: [] for k in ADR_VARIANTS}
    for adr, (home, fx) in ADRS.items():
        if adr not in L or home not in L:
            continue
        a, h = L[adr], L[home]
        f = _fx_ret(md, fx)
        if f is None:
            continue
        y = a["intraday"]
        for label, lag in ADR_VARIANTS.items():
            fx_move = 0.0 if lag is None else _align_after(f, h.index, lag).fillna(0.0)
            x_home = _align_after(h["cc"] - fx_move, a.index, False)   # the home session just before the US day
            resid = x_home - a["gap"]                                  # home moved more than the ADR gapped
            panels[label].append(pd.DataFrame({"date": a.index, "adr": adr, "resid": resid.to_numpy(),
                                               "ret": y.to_numpy()}).dropna())
            if lag is True:
                late = _align_after(a["intraday"], h.index, True)      # ADR's US day -> home's next session
                for sig_name, x, yy, tgt in (("home move (USD) minus ADR gap", resid, y, "ADR open-to-close"),
                                             ("home move (USD)", x_home, y, "ADR open-to-close"),
                                             ("ADR open-to-close (US day)", late, h["intraday"], "home: after its open"),
                                             ("ADR open-to-close (US day)", late, h["gap"], "home: gap")):
                    row = {"adr": adr, "home": home, "signal": sig_name, "target": tgt}
                    for tag, (a0, b0) in (("2006_14", P1), ("2015_26", P2)):
                        row[f"corr_{tag}"], row[f"t_{tag}"], row[f"n_{tag}"] = _corr_t(x[a0:b0], yy[a0:b0])
                    rows.append(row)
    book = []
    for label, parts in panels.items():
        if parts:
            book += _adr_book(pd.concat(parts, ignore_index=True), label)
    return pd.DataFrame(rows), pd.DataFrame(book)


SPLIT_ALPACA = "2021-01-01"


def _book_daily(p: pd.DataFrame) -> tuple[pd.Series, float]:
    """Equal-weight long/short by the residual's sign; direction fixed on 2016-2020."""
    pos = np.sign(p["resid"])
    s1 = p[p["date"] < SPLIT_ALPACA]
    d = np.sign((pos[s1.index] * s1["ret"]).mean()) if len(s1) else 1.0
    if not np.isfinite(d) or d == 0:
        d = 1.0
    return (d * pos * p["ret"]).groupby(p["date"]).mean(), d


def adr_frames(adrs: list[str], start: str = "2016-01-01") -> dict[str, pd.DataFrame]:
    """Per ADR and US day: previous close, official open, close (SIP daily bars), the last pre-market
    trade before 9:25 (IEX - the feed the live trader can see for free) and the 9:35 price (SIP)."""
    from ..data.intraday import AlpacaBars, bars_to_frame

    end = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)).isoformat()
    t0 = pd.Timestamp(start, tz="UTC").isoformat()
    out = {}
    for feed, tf in (("sip", "1Day"), ("iex", "5Min"), ("sip", "5Min")):
        api = AlpacaBars(feed=feed)
        for i in range(0, len(adrs), 10):
            got = api.bars(adrs[i:i + 10], tf, t0, end)
            for sym, rows in got.items():
                f = bars_to_frame(rows, regular_hours=False)
                if f.empty:
                    continue
                day = f.index.tz_localize(None).normalize()
                d = out.setdefault(sym, {})
                if tf == "1Day":
                    d["open"], d["close"] = (pd.Series(f["open"].to_numpy(), index=day),
                                             pd.Series(f["close"].to_numpy(), index=day))
                else:
                    mins = f.index.hour * 60 + f.index.minute
                    if feed == "iex":
                        pre = f[(mins >= 4 * 60) & (mins <= 9 * 60 + 20)]
                        d["pre"] = pd.Series(pre["close"].to_numpy(), index=day[(mins >= 240) & (mins <= 560)]
                                             ).groupby(level=0).last()
                    else:
                        b = f[mins == 9 * 60 + 30]
                        d["p935"] = pd.Series(b["close"].to_numpy(), index=day[mins == 570]).groupby(level=0).last()
        LOG.info("ADR bars: %s %s done", feed, tf)
    frames = {}
    for sym, d in out.items():
        if "close" not in d:
            continue
        f = pd.DataFrame({k: v for k, v in d.items()})
        f["prev_close"] = f["close"].shift(1)
        frames[sym] = f
    return frames


def adr_executable(md, L: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The ADR book as the live trader can run it, on Alpaca data since 2016 (2016-20 picks the direction,
    2021-26 checks it), against the backtest's own reference (the official open)."""
    frames = adr_frames([t for t in ADRS])
    if not frames:
        return pd.DataFrame(), pd.DataFrame()
    panels = {"official open (backtest reference; not executable at the open)": [],
              "pre-market price before 9:25 -> market-on-open (else the last close)": [],
              "pre-market price before 9:25 -> market-on-open (names with a pre-market trade)": [],
              "official open -> enter 9:35 with market orders": []}
    keys = list(panels)
    for adr, (home, fx) in ADRS.items():
        if adr not in frames or home not in L:
            continue
        f = frames[adr]
        h = L[home]
        fr = _fx_ret(md, fx)
        fx_move = _align_after(fr, h.index, True).fillna(0.0) if fr is not None else 0.0
        home_usd = (h["cc"] - fx_move).dropna()
        x = home_usd.reindex(f.index)                       # the home session must be dated the same day
        pc, op, cl = f["prev_close"], f["open"], f["close"]
        pre = f["pre"] if "pre" in f else pd.Series(np.nan, index=f.index)
        p935 = f["p935"] if "p935" in f else pd.Series(np.nan, index=f.index)
        with np.errstate(invalid="ignore", divide="ignore"):
            r_oc = np.log(cl / op).clip(-0.5, 0.5)
            r_935 = np.log(cl / p935).clip(-0.5, 0.5)
            res_open = x - np.log(op / pc)
            res_pre = x - np.log(pre / pc)
            res_pre_fill = x - np.log(pre.fillna(pc) / pc)
        for k, res, ret in ((keys[0], res_open, r_oc), (keys[1], res_pre_fill, r_oc), (keys[2], res_pre, r_oc),
                            (keys[3], res_open, r_935)):
            panels[k].append(pd.DataFrame({"date": f.index, "adr": adr, "market": ADR_MARKET[adr],
                                           "resid": res.to_numpy(), "ret": ret.to_numpy()}).dropna())
    rows, per_mkt = [], []
    for k, parts in panels.items():
        if not parts:
            continue
        p = pd.concat(parts, ignore_index=True)
        daily, d = _book_daily(p)
        n = p.groupby("date").size()
        costs = (3.0, 6.0, 10.0) if "9:35" in k else (0.0, 1.0, 3.0)
        for c in costs:
            net = daily - c / 1e4
            rows.append({"variant": k, "direction": "+" if d > 0 else "-", "cost_bp_round_trip": c,
                         "sharpe_2016_20": _sharpe(net[:"2020"]), "sharpe_2021_26": _sharpe(net["2021":]),
                         "avg_bp_2021_26": float(daily["2021":].mean() * 1e4),
                         "adrs_per_day_2021_26": float(n["2021":].mean())})
        for mkt, g in p.groupby("market"):
            dm, dd = _book_daily(g.reset_index(drop=True))
            per_mkt.append({"variant": k, "market": mkt, "adrs": g["adr"].nunique(), "direction": "+" if dd > 0 else "-",
                            "sharpe_2016_20": _sharpe(dm[:"2020"]), "sharpe_2021_26": _sharpe(dm["2021":]),
                            "avg_bp_2021_26": float(dm["2021":].mean() * 1e4)})
    return pd.DataFrame(rows), pd.DataFrame(per_mkt)


def _xs_weights(sig: pd.DataFrame, frac: float = 0.2) -> pd.DataFrame:
    """Dollar-neutral, gross 1: long the top fifth, short the bottom fifth (at least 3 names a side)."""
    n = sig.notna().sum(axis=1)
    k = np.maximum((n * frac).round(), 3)
    rk = sig.rank(axis=1)
    long_ = rk.gt(n - k, axis=0) & sig.notna()
    short = rk.le(k, axis=0) & sig.notna()
    w = long_.astype(float).div(long_.sum(axis=1).replace(0, np.nan), axis=0) * 0.5 \
        - short.astype(float).div(short.sum(axis=1).replace(0, np.nan), axis=0) * 0.5
    return w.where(n >= 10, 0.0).fillna(0.0)


def market_strategies(md) -> pd.DataFrame:
    rows = []
    for mkt, tickers in STOCKS.items():
        tk = [t for t in tickers if t in md.close.columns]
        if len(tk) < 10:
            continue
        c = md.close[tk]
        live = c.notna().sum(axis=1) >= max(10, len(tk) // 3)
        c = c[live]
        o = md.open[tk].reindex(c.index)
        prev = c.shift(1)
        bad = (o == prev) | (o == c)
        on = np.log(o / prev).mask(bad)                          # overnight (close -> open)
        intra = np.log(c / o).mask(bad)
        cc = np.log(c / prev).clip(-0.5, 0.5)
        nxt_on = on.shift(-1)                                    # tonight's close -> tomorrow's open
        nxt_cc = cc.shift(-1)
        sigs = {
            "overnight persistence (21d overnight sum; close in, open out)":
                (on.rolling(21, min_periods=15).sum(), nxt_on),
            "end-of-day fade (against today's open-to-close; close in, open out)": (-intra, nxt_on),
            "1-day reversal (against today's close-to-close; close to close)": (-cc, nxt_cc),
            "5-day reversal (close to close)": (-cc.rolling(5).sum(), nxt_cc),
        }
        cost, ibkr, note = COSTS.get(mkt, (20.0, False, ""))
        for name, (sig, ret) in sigs.items():
            sig = sig.sub(sig.mean(axis=1), axis=0)
            w = _xs_weights(sig)
            g = (w * ret.clip(-0.5, 0.5)).sum(axis=1, min_count=1).fillna(0.0)
            g = g.where(w.abs().sum(axis=1) > 0)
            s1 = g[P1[0]:P1[1]]
            d = np.sign(s1.mean()) if s1.notna().sum() > 120 else np.sign(g.mean())
            if not np.isfinite(d) or d == 0:
                d = 1.0
            pnl = d * g
            # an overnight book is opened and closed every day: two sides (cost_bp is the round trip) on
            # the gross traded, here 1 per unit of capital in and 1 out; close-to-close books turn over less
            turn = (w.diff().abs().sum(axis=1) / 2) if "close to close" in name else w.abs().sum(axis=1)
            net = pnl - turn * cost / 1e4
            rows.append({"market": mkt, "strategy": name, "direction": "+" if d > 0 else "-",
                         "stocks": len(tk), "sharpe_2006_14": _sharpe(pnl[P1[0]:P1[1]]),
                         "sharpe_2015_26": _sharpe(pnl[P2[0]:P2[1]]),
                         "annual_return_2015_26": float(pnl[P2[0]:P2[1]].mean() * 252),
                         "net_sharpe_2015_26": _sharpe(net[P2[0]:P2[1]]),
                         "net_annual_return_2015_26": float(net[P2[0]:P2[1]].mean() * 252),
                         "round_trip_cost_bp": cost, "on_ibkr": ibkr,
                         "bad_open_share": float(bad.where(c.notna()).mean().mean())})
    return pd.DataFrame(rows)


def data_quality(L: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame([{"ticker": t, "first": str(f.index.min().date()) if len(f) else "", "days": len(f),
                          "bad_open_share": float(f["bad_open"].mean()) if len(f) else np.nan,
                          "bad_open_share_2015_26": float(f.loc["2015":, "bad_open"].mean()) if len(f.loc["2015":]) else np.nan}
                         for t, f in L.items()])


def run(md_us, ctx, out: Path, cfg) -> dict:
    from ..data.loader import download_prices

    fx = sorted({f.removeprefix("1/") for _, f in ADRS.values()})
    tickers = list(dict.fromkeys(list(INDICES.values()) + list(INDEX_ETFS.values()) + list(ADRS) + [h for h, _ in ADRS.values()] + fx
                                 + [t for v in STOCKS.values() for t in v]))
    md = download_prices(tickers, start="2005-01-01")
    LOG.info("Asia: %d of %d tickers downloaded", md.close.shape[1], len(tickers))
    L = legs(md)
    dq = data_quality(L)
    dq.to_csv(out / "asia_data_quality.csv", index=False)
    ll, ll_s = lead_lag(L)
    ee, ee_s = lead_lag(L, {"US": INDICES["US"], **INDEX_ETFS}, etf=True)
    ll, ll_s = pd.concat([ll, ee], ignore_index=True), pd.concat([ll_s, ee_s], ignore_index=True)
    ll.to_csv(out / "asia_leadlag.csv", index=False)
    ll_s.to_csv(out / "asia_leadlag_strategies.csv", index=False)
    adr, adr_s = adr_study(md, L)
    adr.to_csv(out / "asia_adr.csv", index=False)
    adr_s.to_csv(out / "asia_adr_strategy.csv", index=False)
    ex, ex_m = pd.DataFrame(), pd.DataFrame()
    try:
        ex, ex_m = adr_executable(md, L)
        ex.to_csv(out / "asia_adr_executable.csv", index=False)
        ex_m.to_csv(out / "asia_adr_executable_by_market.csv", index=False)
    except Exception as exc:
        LOG.warning("executable ADR study failed (Alpaca keys?): %s", exc)
    ms = market_strategies(md)
    ms.to_csv(out / "asia_market_strategies.csv", index=False)
    costs = pd.DataFrame([{"market": m, "round_trip_cost_bp": c, "on_ibkr": i, "what": n}
                          for m, (c, i, n) in COSTS.items()])
    lines = ["## Asian markets", "",
             "Daily Yahoo data since 2005; directions chosen on 2006-2014, checked on 2015-2026. An Asian session "
             "on date D falls between the US sessions of D-1 and D. Opening prices Yahoo copied from the previous "
             "close are dropped (share per ticker in asia_data_quality.csv).", "",
             "### 1. Lead-lag between the US and Asian indices", "",
             "'gap' = previous close -> open (the news is absorbed here: descriptive); 'after the open' = open -> "
             "close. Each market twice: the index (whose first value of the day still holds yesterday's prices "
             "for stocks that haven't opened yet - Sydney opens in alphabetical groups over 10 minutes - so "
             "'after the open' partly repeats the gap and looks predictable) and an index ETF, whose open is a "
             "price you could actually trade. Only the ETF rows count as tradable evidence; index futures also "
             "trade overnight, so their open has already absorbed the US day.", "",
             ll.round(3).to_markdown(index=False) if len(ll) else "(no data)", "",
             "Trading the sign of the signal on the 'after the open' leg (cost: 0 bp for SPY at the auctions; "
             "2 bp for an index (as if futures, flattering - see above); each ETF at its market's round trip):", "",
             ll_s.round(3).to_markdown(index=False) if len(ll_s) else "(no data)", "",
             "### 2. ADRs vs their home listings", "",
             "Residual = the home listing's last session in dollars minus the ADR's opening gap. Pooled long / "
             "short book on Alpaca (market-on-open in, market-on-close out). Yahoo dates FX bars by their "
             "London / New York close, after the US open, so the clean variant uses the previous day's FX move; "
             "the same-day variant is shown only to measure how much the peek was worth:", "",
             adr_s.round(3).to_markdown(index=False) if len(adr_s) else "(no data)", "",
             "Per ADR (correlations):", "", adr.round(3).to_markdown(index=False) if len(adr) else "(no data)", "",
             "#### As the live trader can run it (Alpaca bars, 2016-20 picks the direction, 2021-26 checks)", "",
             "The backtest's reference price is the official open, which isn't known when market-on-open orders "
             "must be in (9:28). Executable versions: the last pre-market trade before 9:25 on the free IEX feed "
             "(market-on-open in), or entering at 9:35 with market orders (paying the spread).", "",
             ex.round(3).to_markdown(index=False) if len(ex) else "(no Alpaca data)", "",
             "By market:", "", ex_m.round(3).to_markdown(index=False) if len(ex_m) else "(no Alpaca data)", "",
             "### 3. Strategies inside each Asian market (long top fifth / short bottom fifth)", "",
             ms.round(3).to_markdown(index=False) if len(ms) else "(no data)", "",
             "Costs used (round trip at the auctions):", "", costs.to_markdown(index=False), ""]
    (out / "asia.md").write_text("\n".join(lines) + "\n")
    best = ms.sort_values("net_sharpe_2015_26", ascending=False).head(5) if len(ms) else ms
    return {"tickers": int(md.close.shape[1]),
            "leadlag_tradable": ll_s.round(3).to_dict(orient="records") if len(ll_s) else [],
            "adr_strategy": adr_s.round(3).to_dict(orient="records") if len(adr_s) else [],
            "best_market_strategies": best.round(3).to_dict(orient="records") if len(best) else []}
