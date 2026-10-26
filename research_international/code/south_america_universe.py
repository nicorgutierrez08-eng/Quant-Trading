"""South American universes: Brazil, Chile, Argentina, Colombia, Peru, their financials, and their New York ADRs.

* Brazil: the 400 largest domestic companies (Yahoo screener). BDRs (foreign
  companies, tickers ending 31-35 or 39) and real-estate / investment funds
  (FIIs, also quoted as equities; '11' tickers are kept only for companies)
  are removed; one line per company.
* Chile and Argentina: every domestic listing the screener has (local-
  currency accounts; Argentina's CEDEARs report in USD and drop out).
* Colombia: COLCAP members (English Wikipedia), every share class Yahoo
  carries; Peru: S&P/BVL Peru General members (Spanish Wikipedia), plus the
  three listed bank lines. The screener has neither market. After the
  download, keep only the most-traded class of each company
  (`pick_liquid_class`).
* Financials: every financial the screener lists for Brazil, Chile and
  Argentina, by industry; Colombia and Peru flagged by hand from the index
  tables.
* ADRs: South American companies listed in New York, a hand list of those
  trading today (so survivors only, like everything else). They trade in USD,
  can be borrowed, and are the practical way to short Argentina, Colombia
  and Peru.

Survivor caveat as for every other universe: these are companies listed
today.

    python research_international/code/south_america_universe.py --out data_sa
    (download data_sa/universe_south_america.csv and universe_sa_financials.csv with download.py, then)
    python research_international/code/south_america_universe.py --out data_sa --pick-classes data_sa/prices --fin-prices data_sa/prices_fin
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import pandas as pd
import requests
from yfinance import EquityQuery as Q

from deep_universe import FIN_INDUSTRIES, keep, one_line_per_company, screen

SCREENED = {"br": ("Brazil", "BRL", (".SA",), 400), "cl": ("Chile", "CLP", (".SN",), 400), "ar": ("Argentina", "ARS", (".BA",), 400)}
BDR = re.compile(r"^[A-Z0-9]{4}3[1-59]\.SA$")
FUND = re.compile(r"(?i)(\bfundos?\b|\bfund\b|\bfdo\b|\bfd invest|\bfii\b|\bfiagro\b|\bfip\b|imob|investimento no exterior|\bdtvm\b|\bcotas\b)")


def is_fund_or_foreign(x: dict) -> bool:
    """Brazilian funds (FIIs etc.) and foreign units trade as equities; '11' tickers are kept only for companies (S.A.)."""
    sym, name = x["symbol"], str(x.get("longName") or x.get("shortName") or "")
    if BDR.match(sym) or FUND.search(name):
        return True
    return sym.endswith("11.SA") and not re.search(r"S\.?\s?A\.?\s*$", name)

COLOMBIA_FIN = {"BOGOTA", "BCOLOMBIA", "PFBCOLOM", "PFBCOLOMB", "CIBEST", "PFCIBEST", "BVC", "CORFICOLCF", "PFCORFICOL",
                "PFDAVVNDA", "GRUPOAVAL", "PFAVAL", "GRUPOSURA", "PFGRUPSURA", "BOLIVAR"}
COLOMBIA_EXTRA = ["CIBEST", "PFCIBEST", "GEB"]                     # Bancolombia's holding company since 2025; EEB trades as GEB
PERU_FIN = {"BAP", "IFS", "BBVAC1", "RIMSEGC1", "CREDITC1", "SCOTIAC1", "INTERBC1", "GBVLAC1", "AIHC1"}
PERU_EXTRA = ["CREDITC1", "SCOTIAC1", "INTERBC1", "FERREYC1", "VOLCABC1"]

# South American companies with New York listings (ADRs or primary US listings), as of 2026. Embraer trades as EMBJ and
# Copel as ELPC since 2025; Eletrobras (renamed AXIA), BRF (merged into MBRF) and Despegar (acquired) have no usable
# Yahoo history and are left out.
ADRS = {
    "Brazil": "PBR VALE ITUB BBD ABEV SBS GGB SID CIG ELPC BSBR BBDO EMBJ SUZ UGP TIMB VIV BAK NU STNE PAGS XP CSAN VTEX ARCO",
    "Chile": "SQM BCH BSAC LTM CCU ENIC AKO-B",
    "Argentina": "YPF GGAL BMA BBAR SUPV PAM TGS CEPU EDN LOMA CRESY IRS TEO TX GLOB MELI VIST BIOX",
    "Colombia": "EC CIB AVAL TGLS",
    "Peru": "BAP BVN SCCO IFS",
}
ADR_FIN = {"ITUB", "BBD", "BSBR", "BBDO", "NU", "STNE", "PAGS", "XP", "BCH", "BSAC", "GGAL", "BMA", "BBAR", "SUPV", "CIB", "AVAL", "BAP", "IFS"}


def wiki(url: str, col: str) -> pd.DataFrame:
    S = requests.Session()
    S.headers["User-Agent"] = "Mozilla/5.0 (research)"
    return [t for t in pd.read_html(io.StringIO(S.get(url, timeout=30).text)) if col in t.columns][0]


def screened() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, fins = [], []
    for reg, (market, ccy, suf, top) in SCREENED.items():
        qs = [x for x in screen(Q("and", [Q("eq", ["region", reg]), Q("gt", ["intradaymarketcap", 0])]), total_cap=2000)
              if keep(x, ccy, suf) and not is_fund_or_foreign(x)]
        qs = sorted(qs, key=lambda x: -(x.get("marketCap") or 0))[:top]
        ind_of = {}
        for ind in FIN_INDUSTRIES:
            for x in screen(Q("and", [Q("eq", ["region", reg]), Q("eq", ["industry", ind])]), total_cap=500):
                if keep(x, ccy, suf) and not is_fund_or_foreign(x):
                    ind_of[x["symbol"]] = ind
                    fins.append({"market": market, "ticker": x["symbol"], "name": x.get("longName") or x.get("shortName"),
                                 "industry": ind, "market_cap": x.get("marketCap"), "financial": True})
        for x in qs:
            rows.append({"market": market, "ticker": x["symbol"], "name": x.get("longName") or x.get("shortName"),
                         "industry": ind_of.get(x["symbol"]), "market_cap": x.get("marketCap"), "financial": x["symbol"] in ind_of})
        print(f"{market:10s} {len(qs)} names, {len(ind_of)} financials listed")
    return pd.DataFrame(rows), pd.DataFrame(fins)


def colombia() -> pd.DataFrame:
    t = wiki("https://en.wikipedia.org/wiki/COLCAP", "Symbol").dropna(subset=["Symbol"])
    rows = []
    for _, r in t.iterrows():
        for code in re.findall(r"BVC:\s*([A-Z]+)", str(r["Symbol"])):
            rows.append({"market": "Colombia", "ticker": f"{code}.CL", "name": r["Company"], "industry": r["Industry"],
                         "financial": code in COLOMBIA_FIN})
    rows += [{"market": "Colombia", "ticker": f"{c}.CL", "name": {"GEB": "Grupo Energía Bogotá"}.get(c, "Grupo Cibest"),
              "industry": None, "financial": c in COLOMBIA_FIN} for c in COLOMBIA_EXTRA]
    return pd.DataFrame(rows).drop_duplicates("ticker")


def peru() -> pd.DataFrame:
    t = wiki("https://es.wikipedia.org/wiki/S%26P/BVL_Peru_General", "Símbolo")
    rows = []
    for _, r in t.iterrows():
        for code in re.findall(r"BVL:\s*([A-Z0-9]+)", str(r["Símbolo"])):
            rows.append({"market": "Peru", "ticker": f"{code}.LM", "name": r["Compañía"], "industry": r["Industria"],
                         "financial": code in PERU_FIN})
    rows += [{"market": "Peru", "ticker": f"{c}.LM", "name": c, "industry": None, "financial": c in PERU_FIN} for c in PERU_EXTRA]
    return pd.DataFrame(rows).drop_duplicates("ticker")


def adrs() -> pd.DataFrame:
    return pd.DataFrame([{"market": "South America ADRs", "ticker": t, "name": t, "industry": country, "financial": t in ADR_FIN}
                         for country, v in ADRS.items() for t in v.split()])


def pick_liquid_class(universe: pd.DataFrame, prices: Path, market: str) -> pd.DataFrame:
    """Keep the most-traded line of each company (Colombian and Peruvian companies list several share classes)."""
    d = prices / market
    c, v = pd.read_parquet(d / "close.parquet"), pd.read_parquet(d / "volume.parquet")
    tv = (c * v).iloc[-500:].median()
    u = universe[universe["market"] == market].copy()
    u["tv"] = u["ticker"].map(tv).fillna(-1)
    u = u[u["ticker"].isin(c.columns[c.notna().sum() > 252])]
    u = u.sort_values("tv", ascending=False).drop_duplicates("name")
    return u.drop(columns="tv")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data_sa")
    ap.add_argument("--pick-classes", help="after downloading: prices folder; keeps one share class per company in Colombia and Peru")
    ap.add_argument("--fin-prices", help="with --pick-classes: the financials price folder, trimmed the same way")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.pick_classes:
        u = pd.read_csv(out / "universe_south_america.csv")
        keep_ = [pick_liquid_class(u, Path(args.pick_classes), mk) for mk in ("Colombia", "Peru")]
        u = pd.concat([u[~u["market"].isin(["Colombia", "Peru"])], *keep_], ignore_index=True)
        u.to_csv(out / "universe_south_america.csv", index=False)
        # the lab trades every column of a market's price folder, so drop the other share classes from the files too
        f = pd.read_csv(out / "universe_sa_financials.csv")
        for mk in ("Colombia", "Peru"):
            chosen = set(u.loc[u["market"] == mk, "ticker"])
            for root in [Path(args.pick_classes)] + ([Path(args.fin_prices)] if args.fin_prices else []):
                for pq in (root / mk).glob("*.parquet"):
                    x = pd.read_parquet(pq)
                    x[[c for c in x.columns if c in chosen]].to_parquet(pq)
            f = f[~((f["market"] == mk) & ~f["ticker"].isin(chosen))]
        f.to_csv(out / "universe_sa_financials.csv", index=False)
        print(u.groupby("market").agg(names=("ticker", "size"), financials=("financial", "sum")).to_string())
        return
    s, fins = screened()
    u = pd.concat([one_line_per_company(s), colombia(), peru()], ignore_index=True)
    u.to_csv(out / "universe_south_america.csv", index=False)
    f = pd.concat([one_line_per_company(fins.drop_duplicates("ticker")), u[u["market"].isin(["Colombia", "Peru"]) & u["financial"]]],
                  ignore_index=True)
    f.to_csv(out / "universe_sa_financials.csv", index=False)
    a = adrs()
    a.to_csv(out / "universe_sa_adrs.csv", index=False)
    print(u.groupby("market").agg(names=("ticker", "size"), financials=("financial", "sum")).to_string())
    print(f.groupby(["market", "industry"]).size().to_string())
    print(f"ADRs: {len(a)} ({a['financial'].sum()} financials)")


if __name__ == "__main__":
    main()
