"""International stock universes from current index constituent lists.

Each market's universe is today's members of its main index, scraped from
Wikipedia (English, or the local-language page where the English one has no
list), mapped to Yahoo Finance tickers and tagged with a sector and a
financials flag. Like the US universe, these are *today's* members, so every
backtest on them carries survivorship bias; see the report.

    python research_international/code/universes.py --out data/intl/universe.csv
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

WIKI = "https://{lang}.wikipedia.org/wiki/{page}"
FIN_WORDS = ("financ", "bank", "insur", "capital market", "brokerage", "asset manage", "diversified fin",
             "real estate investment trust", "reit", "exchange", "lending", "credit", "invest")
# Hang Seng Index sub-index names and the like that mean "financials"
FIN_LABELS = {"finance", "financials", "financial", "financial services", "banks", "insurance"}


def _get(session, lang, page):
    r = session.get(WIKI.format(lang=lang, page=page), timeout=40)
    r.raise_for_status()
    return r.text


def _tables(html):
    return pd.read_html(io.StringIO(html))


def _flat(df):
    df = df.copy()
    df.columns = [" ".join(map(str, c)).strip() if isinstance(c, tuple) else str(c) for c in df.columns]
    return df


def _col(df, *keys):
    for c in df.columns:
        lc = c.lower()
        if any(k in lc for k in keys):
            return c
    return None


def is_financial(sector: str) -> bool:
    s = (sector or "").lower().strip()
    if s in FIN_LABELS:
        return True
    return any(w in s for w in FIN_WORDS) and "real estate" not in s.replace("real estate investment trust", "")


def table_universe(session, page, market, index, suffix, code_keys, sector_keys=("sector", "industry", "segment", "sub-index"),
                   name_keys=("company", "name", "constituent", "securities"), min_rows=20, lang="en", code_fmt=None):
    html = _get(session, lang, page)
    best = None
    for t in _tables(html):
        t = _flat(t)
        if t.shape[0] < min_rows:
            continue
        c = _col(t, *code_keys)
        if c is None:
            continue
        if best is None or t.shape[0] > best.shape[0]:
            best = t
    if best is None:
        raise ValueError(f"no constituent table on {page}")
    c, s, n = _col(best, *code_keys), _col(best, *sector_keys), _col(best, *name_keys)
    out = pd.DataFrame({"code": best[c].astype(str).str.strip(),
                        "name": best[n].astype(str) if n else "",
                        "sector": best[s].astype(str) if s else ""})
    out["code"] = out["code"].str.replace(r"^[A-Z]+:\s*", "", regex=True).str.replace(r"\s+", "", regex=True)
    out = out[out["code"].notna() & ~out["code"].astype(str).str.lower().isin(["nan", "none", ""])]   # pandas 3 keeps NaN through astype(str)
    if code_fmt:
        out["code"] = out["code"].map(code_fmt)
    out = out[out["code"].str.len() > 0]
    out["ticker"] = out["code"].map(lambda x: x if suffix is None else f"{x}{suffix}")
    out["market"], out["index"] = market, index
    return out


# -----------------------------------------------------------------------------
# market-specific parsers
# -----------------------------------------------------------------------------
def japan_nikkei225(session):
    html = _get(session, "ja", "%E6%97%A5%E7%B5%8C%E5%B9%B3%E5%9D%87%E6%A0%AA%E4%BE%A1")
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for tab in soup.select("table"):
        head = [th.get_text(strip=True) for th in tab.select("tr th")][:3]
        if "証券コード" not in head:
            continue
        h = tab.find_previous(["h3", "h4", "h2"])
        sector = re.sub(r"（.*?）", "", h.get_text(strip=True)) if h else ""
        for tr in tab.select("tr")[1:]:
            tds = [td.get_text(strip=True) for td in tr.select("td")]
            if tds and re.fullmatch(r"\d{4}|\d{3}[A-Z]", tds[0]):
                rows.append((tds[0], tds[1] if len(tds) > 1 else "", sector))
    df = pd.DataFrame(rows, columns=["code", "name", "sector"]).drop_duplicates("code")
    jp_fin = ("銀行", "保険", "証券", "その他金融")
    df["financial"] = df["sector"].map(lambda s: any(k in s for k in jp_fin))
    df["ticker"] = df["code"] + ".T"
    df["market"], df["index"] = "Japan", "Nikkei 225"
    return df


def taiwan50(session):
    html = _get(session, "zh", "%E8%87%BA%E7%81%A350%E6%8C%87%E6%95%B8")
    t = _tables(html)[0]
    t = _flat(t)
    codes = pd.concat([t.iloc[:, 0], t.iloc[:, 3]]).astype(str).str.extract(r"(\d{4})")[0].dropna()
    names = pd.concat([t.iloc[:, 1], t.iloc[:, 4]]).astype(str)
    df = pd.DataFrame({"code": codes.values, "name": names.iloc[: len(codes)].values})
    # TWSE industry code 28 = finance and insurance
    df["sector"] = df["code"].map(lambda c: "Finance & insurance" if c.startswith("28") else "")
    df["financial"] = df["code"].str.startswith("28")
    df["ticker"] = df["code"] + ".TW"
    df["market"], df["index"] = "Taiwan", "Taiwan 50"
    return df


def china_csi300(session):
    df = table_universe(session, "CSI_300_Index", "China", "CSI 300", None, ("ticker",), sector_keys=("segment",),
                        code_fmt=lambda x: re.sub(r"\D", "", x).zfill(6))
    df["ticker"] = df["code"].map(lambda c: f"{c}.SS" if c.startswith("6") else f"{c}.SZ")
    return df


def singapore_sti(session):
    df = table_universe(session, "Straits_Times_Index", "Singapore", "STI", ".SI", ("stock symbol", "symbol"), min_rows=20)
    fin = {"D05", "O39", "U11", "S68", "G07"}            # DBS, OCBC, UOB, SGX, Great Eastern
    df["sector"] = df["code"].map(lambda c: "Financials" if c in fin else "")
    return df


SOURCES = {
    # Asia-Pacific
    "Japan": japan_nikkei225,
    "Hong Kong": lambda s: table_universe(s, "Hang_Seng_Index", "Hong Kong", "Hang Seng", ".HK", ("ticker",),
                                          code_fmt=lambda x: re.sub(r"\D", "", x).zfill(4)),
    "Hong Kong (H-shares)": lambda s: table_universe(s, "Hang_Seng_China_Enterprises_Index", "Hong Kong (H-shares)", "HSCEI",
                                                     ".HK", ("ticker",), code_fmt=lambda x: re.sub(r"\D", "", x).zfill(4)),
    "China": china_csi300,
    "Korea": lambda s: table_universe(s, "KOSPI_200", "Korea", "KOSPI 200", ".KS", ("symbol",),
                                      code_fmt=lambda x: re.sub(r"\D", "", x).zfill(6)),
    "Taiwan": taiwan50,
    "Singapore": singapore_sti,
    "Australia": lambda s: table_universe(s, "S%26P/ASX_200", "Australia", "ASX 200", ".AX", ("code",)),
    "India": lambda s: pd.concat([
        table_universe(s, "NIFTY_50", "India", "NIFTY 50", ".NS", ("symbol",)),
        table_universe(s, "NIFTY_Next_50", "India", "NIFTY Next 50", ".NS", ("symbol",))]),
    "Malaysia": lambda s: table_universe(s, "FTSE_Bursa_Malaysia_KLCI", "Malaysia", "KLCI", ".KL", ("stock code",),
                                         code_fmt=lambda x: re.sub(r"\D", "", x).zfill(4)),
    "Thailand": lambda s: table_universe(s, "SET50_Index_and_SET100_Index", "Thailand", "SET50", ".BK", ("symbol",)),
    "New Zealand": lambda s: table_universe(s, "S%26P/NZX_50_Index", "New Zealand", "NZX 50", ".NZ", ("ticker",)),
    # Europe and Canada
    "UK": lambda s: table_universe(s, "FTSE_100_Index", "UK", "FTSE 100", ".L", ("ticker",),
                                   code_fmt=lambda x: x.replace(".", "-").rstrip("-")),
    "Germany": lambda s: table_universe(s, "DAX", "Germany", "DAX", ".DE", ("ticker",),
                                        code_fmt=lambda x: x.split(".")[0]),
    "France": lambda s: table_universe(s, "CAC_40", "France", "CAC 40", ".PA", ("ticker",),
                                       code_fmt=lambda x: x.split(".")[0]),
    "Switzerland": lambda s: table_universe(s, "Swiss_Market_Index", "Switzerland", "SMI", ".SW", ("ticker",),
                                            code_fmt=lambda x: x.split(".")[0], min_rows=15),
    "Netherlands": lambda s: table_universe(s, "AEX_index", "Netherlands", "AEX", ".AS", ("ticker",),
                                            code_fmt=lambda x: x.split(".")[0]),
    "Spain": lambda s: table_universe(s, "IBEX_35", "Spain", "IBEX 35", ".MC", ("ticker",),
                                      code_fmt=lambda x: x.split(".")[0]),
    "Italy": lambda s: table_universe(s, "FTSE_MIB", "Italy", "FTSE MIB", ".MI", ("ticker",),
                                      code_fmt=lambda x: x.split(".")[0]),
    "Sweden": lambda s: table_universe(s, "OMX_Stockholm_30", "Sweden", "OMXS30", ".ST", ("ticker",),
                                       code_fmt=lambda x: x.split(".")[0].replace(" ", "-")),
    "Canada": lambda s: table_universe(s, "S%26P/TSX_60", "Canada", "TSX 60", ".TO", ("symbol",),
                                       code_fmt=lambda x: x.split(".")[0].replace(".", "-")),
}


def build(markets=None) -> pd.DataFrame:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (research; quant-trading)"
    parts = []
    for m, fn in SOURCES.items():
        if markets and m not in markets:
            continue
        try:
            df = fn(s)
            if "financial" not in df:
                df["financial"] = df["sector"].map(is_financial)
            parts.append(df[["market", "index", "ticker", "code", "name", "sector", "financial"]])
            print(f"{m:22s} {len(df):4d} names, {int(df['financial'].sum()):3d} financials")
        except Exception as exc:  # noqa: BLE001 - one market must not stop the rest
            print(f"{m:22s} FAILED: {type(exc).__name__}: {str(exc)[:80]}")
    out = pd.concat(parts, ignore_index=True)
    return out.drop_duplicates(["market", "ticker"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/intl/universe.csv")
    args = ap.parse_args(argv)
    u = build()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    u.to_csv(args.out, index=False)
    print(f"\n{len(u)} names in {u['market'].nunique()} markets, {int(u['financial'].sum())} financials -> {args.out}")


if __name__ == "__main__":
    main()
