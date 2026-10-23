"""Deeper universes: every listed Asia-Pacific financial, plus 18 more exchanges.

The first pass used index members (1,760 names, 308 financials). Here the
Yahoo equity screener supplies, by region:

* **Asia-Pacific financials, all listed** - every equity Yahoo classes in the
  Financial Services sector, by industry (regional banks, diversified banks,
  life / P&C insurers, capital markets, credit services, ...), so financials
  can be studied within industry and not just as one bucket;
* **new exchanges** - the largest domestic companies by market cap in
  Indonesia, Brazil, Mexico, South Africa, Turkey, Saudi Arabia, Israel,
  Poland, Norway, Denmark, Finland, Belgium, Portugal, Greece, Chile, Kuwait
  and Qatar, with their sector, plus Pakistan (KSE-100 from Wikipedia), and
  hand lists for Vietnam (largest HOSE names) and Austria (ATX Prime; Vienna's
  screener results are mostly foreign companies on its global segment).

Foreign cross-listings (Brazilian BDRs, Mexico's SIC, Thai DRs, Chilean
CL listings) are removed by requiring the
company's financial statements to be in the local currency (Israel exempt:
many Israeli companies report in USD and Tel Aviv has few foreign lines).

Bias: like index lists, the screener only returns companies listed today, so
every universe here is a survivor universe. It is worse for small names than
for index members; signals that favour small or illiquid stocks are suspect.

    python research_international/code/deep_universe.py --out data2
"""
from __future__ import annotations

import argparse
import io
import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf
from yfinance import EquityQuery as Q

FIN_INDUSTRIES = ["Banks—Regional", "Banks—Diversified", "Insurance—Life", "Insurance—Property & Casualty",
                  "Insurance—Diversified", "Insurance—Reinsurance", "Insurance—Specialty", "Insurance Brokers",
                  "Capital Markets", "Asset Management", "Credit Services", "Financial Data & Stock Exchanges",
                  "Financial Conglomerates", "Mortgage Finance"]

# region -> (market name, local currency, allowed symbol suffixes)
ASIA = {
    "jp": ("Japan", "JPY", (".T",)), "kr": ("Korea", "KRW", (".KS", ".KQ")), "tw": ("Taiwan", "TWD", (".TW", ".TWO")),
    "hk": ("Hong Kong", None, (".HK",)), "cn": ("China", "CNY", (".SS", ".SZ")), "in": ("India", "INR", (".NS",)),
    "id": ("Indonesia", "IDR", (".JK",)), "sg": ("Singapore", None, (".SI",)), "my": ("Malaysia", "MYR", (".KL",)),
    "th": ("Thailand", "THB", (".BK",)), "au": ("Australia", "AUD", (".AX",)), "nz": ("New Zealand", "NZD", (".NZ",)),
}
NEW = {
    "id": ("Indonesia", "IDR", (".JK",)), "br": ("Brazil", "BRL", (".SA",)), "mx": ("Mexico", "MXN", (".MX",)),
    "za": ("South Africa", "ZAR", (".JO",)), "tr": ("Turkey", "TRY", (".IS",)), "sa": ("Saudi Arabia", "SAR", (".SR",)),
    "il": ("Israel", None, (".TA",)), "pl": ("Poland", "PLN", (".WA",)), "no": ("Norway", "NOK", (".OL",)),
    "dk": ("Denmark", "DKK", (".CO",)), "fi": ("Finland", "EUR", (".HE",)), "be": ("Belgium", "EUR", (".BR",)),
"pt": ("Portugal", "EUR", (".LS",)), "gr": ("Greece", "EUR", (".AT",)),
    "cl": ("Chile", "CLP", (".SN",)), "kw": ("Kuwait", "KWD", (".KW",)), "qa": ("Qatar", "QAR", (".QA",)),
}
TOP_N = 120

# Vienna's screener results are mostly Eurozone companies on its global segment; use ATX Prime names instead.
AUSTRIA = {"fin": "EBS BG RBI VIG UQA OBS",
           "other": "VER OMV ANDR WIE EVN POST CAI VOE LNZ SBO MMK DOC ATS IIA TKA STR AGR FACC PAL SEM ZAG KTCG FLU PYT AMAG ROS WXF"}

# Largest HOSE names (VN30 + VN100 members as of 2025-26); financial flag = banks, brokers, insurers.
VIETNAM = {
    "fin": "ACB BID CTG HDB MBB SHB SSB STB TCB TPB VCB VIB VPB LPB EIB MSB OCB BVH SSI VCI HCM VND FTS BSI AGR CTS VIX ORS EVF BMI MIG PGI NAB",
    "other": "BCM FPT GAS GVR HPG MSN MWG PLX POW SAB VHM VIC VJC VNM VRE DGC DIG DXG GMD KBC KDH NLG NVL PDR PNJ REE VHC DCM DPM "
             "FRT GEX HAG HSG KDC NKG PVD PVT SBT SZC VGC VCG CII CTD DGW HHV HDG IJC PC1 VSH BMP DHG IMP TCH SCS NT2 PHR DPR ASM "
             "BWE HT1 KOS CMG CSV DBC ANV IDI HQC ITA DBD TLG SIP BAF LHG PAN TNH VPI CRE NTL HDC DXS SKG",
}


def screen(query, total_cap: int = 2000) -> list[dict]:
    out, offset = [], 0
    while offset < total_cap:
        for attempt in range(3):
            try:
                r = yf.screen(query, size=250, offset=offset, sortField="intradaymarketcap", sortAsc=False)
                break
            except Exception:  # noqa: BLE001
                time.sleep(3 * (attempt + 1))
        else:
            break
        qs = r.get("quotes", [])
        out += qs
        if len(qs) < 250 or offset + 250 >= r.get("total", 0):
            break
        offset += 250
        time.sleep(0.5)
    return out


def keep(x: dict, ccy: str | None, suffixes: tuple[str, ...]) -> bool:
    sym = str(x.get("symbol", ""))
    if x.get("quoteType") != "EQUITY" or not sym.endswith(suffixes):
        return False
    if ccy and x.get("financialCurrency") not in (ccy, None):
        return False
    return True


def asia_financials() -> pd.DataFrame:
    rows = []
    for reg, (market, ccy, suf) in ASIA.items():
        n0 = len(rows)
        for ind in FIN_INDUSTRIES:
            q = Q("and", [Q("eq", ["region", reg]), Q("eq", ["industry", ind])])
            for x in screen(q):
                if keep(x, ccy, suf):
                    rows.append({"market": market, "ticker": x["symbol"], "name": x.get("longName") or x.get("shortName"),
                                 "industry": ind, "market_cap": x.get("marketCap"), "currency": x.get("currency")})
        print(f"{market:12s} {len(rows) - n0} financials")
    df = pd.DataFrame(rows).drop_duplicates("ticker")
    df["financial"] = True
    df["universe"] = "asia_financials_all"
    return df


def new_markets() -> pd.DataFrame:
    rows = []
    for reg, (market, ccy, suf) in NEW.items():
        qs = [x for x in screen(Q("and", [Q("eq", ["region", reg]), Q("gt", ["intradaymarketcap", 0])]), total_cap=1500)
              if keep(x, ccy, suf)]
        qs = sorted(qs, key=lambda x: -(x.get("marketCap") or 0))[:TOP_N]
        fin = set()
        for ind in FIN_INDUSTRIES:                       # sector flag via an industry query (quotes carry no sector)
            fin |= {x["symbol"] for x in screen(Q("and", [Q("eq", ["region", reg]), Q("eq", ["industry", ind])]), total_cap=500)}
        for x in qs:
            rows.append({"market": market, "ticker": x["symbol"], "name": x.get("longName") or x.get("shortName"),
                         "industry": None, "market_cap": x.get("marketCap"), "currency": x.get("currency"),
                         "financial": x["symbol"] in fin})
        print(f"{market:12s} {len(qs)} names, {sum(x['symbol'] in fin for x in qs)} financials")
    pk = pakistan()
    vn = pd.DataFrame([{"market": "Vietnam", "ticker": f"{t}.VN", "financial": k == "fin"} for k, v in VIETNAM.items() for t in v.split()])
    at = pd.DataFrame([{"market": "Austria", "ticker": f"{t}.VI", "financial": k == "fin"} for k, v in AUSTRIA.items() for t in v.split()])
    df = pd.concat([pd.DataFrame(rows), pk, vn, at], ignore_index=True)
    df["universe"] = "new_markets_top"
    return df


def one_line_per_company(df: pd.DataFrame) -> pd.DataFrame:
    """Dual share classes (PETR3/PETR4, CARL-A/CARL-B, KESKOA/KESKOB) would be two near-identical bets; keep the
    first line (largest market cap) of each company within a market."""
    key = df["name"].fillna(df["ticker"]).astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    return df.loc[~pd.Series(list(zip(df["market"], key)), index=df.index).duplicated()].reset_index(drop=True)


def pakistan() -> pd.DataFrame:
    S = requests.Session()
    S.headers["User-Agent"] = "Mozilla/5.0 (research)"
    t = [x for x in pd.read_html(io.StringIO(S.get("https://en.wikipedia.org/wiki/KSE_100_Index", timeout=30).text))
         if "PSX sector" in x.columns][0]
    fin = t["PSX sector"].astype(str).str.contains("Bank|Insurance|Invest|Leasing|Modaraba|Financ", case=False)
    print(f"Pakistan     {len(t)} names, {int(fin.sum())} financials")
    return pd.DataFrame({"market": "Pakistan", "ticker": t["Ticker"].astype(str).str.replace(r"^PSX:\s*", "", regex=True).str.strip() + ".KA", "name": t["Company"],
                         "industry": t["PSX sector"], "financial": fin.values})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data2")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    a = one_line_per_company(asia_financials())
    a.to_csv(out / "universe_asia_financials.csv", index=False)
    b = one_line_per_company(new_markets())
    b.to_csv(out / "universe_new_markets.csv", index=False)
    print(a.groupby(["market", "industry"]).size().unstack(fill_value=0).to_string())
    print(f"Asia-Pacific financials: {len(a)}; new markets: {len(b)} names in {b['market'].nunique()} markets")


if __name__ == "__main__":
    main()
