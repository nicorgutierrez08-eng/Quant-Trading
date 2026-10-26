"""News / media correlation scan: timing, parsing and a planted correlation it must find."""
import numpy as np
import pandas as pd

from qtrade.data import make_market
from qtrade.data.media import Store, parse_gdelt, short_name
from qtrade.research import news_zoo as Z

NY = "America/New_York"


def test_names_and_gdelt_parsing():
    assert short_name("Apple Inc.") == "Apple"
    assert short_name("The Home Depot, Inc.") == "Home Depot"
    assert short_name("Costco") == "Costco"
    p = {"query_details": {"date_resolution": "day"},
         "timeline": [{"series": "CNN", "data": [{"date": "20170101T120000Z", "value": 0.5},
                                                 {"date": "20170102T120000Z", "value": 0.0}]},
                      {"series": "FOX", "data": [{"date": "20170101T120000Z", "value": 0.25}]}]}
    s = parse_gdelt(p)
    assert s.loc["2017-01-01"] == 0.75 and s.loc["2017-01-02"] == 0.0
    v = parse_gdelt({"timeline": [{"data": [{"date": "20170101T000000Z", "value": 3, "norm": 100}]}]}, total=True)
    assert v.iloc[0] == 100
    assert parse_gdelt({}) is None


def test_store_is_incremental(tmp_path):
    st = Store(tmp_path / "x.parquet")
    st.add("A", pd.Series([1.0, 2.0], index=pd.to_datetime(["2020-01-01", "2020-01-02"])))
    st.add("B", None)
    st.save()
    again = Store(tmp_path / "x.parquet")
    assert again.has("A") and again.has("B") and not again.has("C")
    assert list(again.df.columns) == ["A"]


def test_entry_timing():
    dates = pd.bdate_range("2024-01-01", periods=10)            # Mon 1 Jan ... (holidays ignored here)
    # a GDELT / Wikipedia day d is used from the next session's open
    assert list(Z.entry_of_days(pd.to_datetime(["2024-01-01", "2024-01-06"]), dates)) == [1, 5]
    # an article before 9:30 is used at that day's open; after 9:30 at the next one
    ts = pd.Series(pd.to_datetime(["2024-01-03 08:00", "2024-01-03 10:00", "2024-01-05 18:00"]).tz_localize(NY))
    assert list(Z.entry_of_times(ts, dates)) == [2, 3, 5]


def test_hn_mentions():
    hn = pd.DataFrame({"title": ["Apple announces new chip", "Home Depot hacked", "apple pie recipe", "Gap sale"],
                       "created_at": pd.to_datetime(["2020-01-01"] * 4, utc=True), "points": [100, 50, 10, 5]})
    m = Z.hn_mentions(hn, {"AAPL": "Apple", "HD": "Home Depot", "GAP": "Gap"})
    assert sorted(m["ticker"]) == ["AAPL", "HD"]               # case-sensitive; 3-letter names skipped (too ambiguous)


def test_scan_finds_a_planted_correlation():
    md, _ = make_market(n_stocks=80, n_days=900, seed=4, start="2019-01-02")
    tg = {k: v.to_numpy(dtype=float) for k, v in Z.targets(md).items()}
    nxt = Z.targets(md)["next_1d"]
    rng = np.random.default_rng(0)
    planted = 0.3 * nxt.rank(axis=1, pct=True) + rng.normal(size=nxt.shape)       # leaks a bit of tomorrow
    noise = pd.DataFrame(rng.normal(size=nxt.shape), index=nxt.index, columns=nxt.columns)
    mask = pd.DataFrame(True, index=md.dates, columns=md.tickers)
    rows = pd.DataFrame(Z.scan_cross({"planted": planted, "noise": noise}, tg, mask, "test"))
    p = rows[(rows.feature == "planted") & (rows.target == "next_1d")].iloc[0]
    n = rows[(rows.feature == "noise") & (rows.target == "next_1d")].iloc[0]
    assert p["t_all"] > 5 and p["spread_bp_all"] > 0 and abs(n["t_all"]) < 4


def test_count_features_and_market_scan():
    idx = pd.bdate_range("2018-01-01", periods=400)
    C = pd.DataFrame({"A": np.r_[np.ones(300), 10 * np.ones(100)]}, index=idx)
    f = Z.count_features("x", C)
    assert f["x:abnormal"]["A"].iloc[301] > 1 and f["x:spike"]["A"].iloc[301] == 1.0
    px = pd.DataFrame({"SPY": 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, 1500)))},
                      index=pd.bdate_range("2017-01-02", periods=1500))
    lead = np.log(px["SPY"]).shift(-1) - np.log(px["SPY"])
    rows = pd.DataFrame(Z.scan_market({"lead": lead + np.random.default_rng(2).normal(0, 0.01, 1500)}, px))
    r = rows[(rows.horizon == "next_1d")].iloc[0]
    assert r["t_A"] > 5 and r["t_B"] > 5


def test_collect_gdelt_resumes(tmp_path, monkeypatch):
    import time

    from qtrade.data import media as M

    calls = []

    def fake(api, url, query, mode, start=M.START, end=None):
        calls.append((query, mode))
        if query == '"Nobody"':
            return {"timeline": []}
        return {"query_details": {"date_resolution": "day"},
                "timeline": [{"data": [{"date": "20170101T000000Z", "value": 5, "norm": 900},
                                       {"date": "20170102T000000Z", "value": 7, "norm": 950}]}]}

    monkeypatch.setattr(M, "_gdelt", fake)
    keys = {"AAA": '"Aaa"', "NOB": '"Nobody"'}
    left = M.collect_gdelt(keys, "gdelt_company", M.GDELT_DOC, ("timelinevolraw",), tmp_path, time.time() + 60, None)
    assert left == 0 and len(calls) == 2
    v = pd.read_parquet(tmp_path / "gdelt_company_timelinevolraw.parquet")
    assert list(v.columns) == ["AAA"] and v["AAA"].sum() == 12
    assert pd.read_parquet(tmp_path / "gdelt_total_articles.parquet")["all"].sum() == 1850
    M.collect_gdelt(keys, "gdelt_company", M.GDELT_DOC, ("timelinevolraw",), tmp_path, time.time() + 60, None)
    assert len(calls) == 2                                      # nothing fetched twice
    left = M.collect_gdelt({"CCC": '"C"'}, "gdelt_company", M.GDELT_DOC, ("timelinevolraw",), tmp_path,
                           time.time() - 1, None)
    assert left == 1                                            # out of time: reported as still to fetch


def test_gdelt_refusals_are_retried_not_recorded_as_empty(tmp_path, monkeypatch):
    import time

    from qtrade.data import media as M

    calls = []

    def fake(api, url, query, mode, start=M.START, end=None):
        calls.append(query)
        if query == '"Throttled"':
            return M.FAILED                       # 429: no yearly fallback, no "empty" record
        if query == '"X"':
            return None                           # GDELT's error text: genuinely nothing to fetch
        return {"query_details": {"date_resolution": "day"},
                "timeline": [{"data": [{"date": "20170101T000000Z", "value": 5, "norm": 900}]}]}

    monkeypatch.setattr(M, "_gdelt", fake)
    monkeypatch.setattr(M.time, "sleep", lambda s: None)
    keys = {"THR": '"Throttled"', "X": '"X"', "OK": '"Fine"'}
    left = M.collect_gdelt(keys, "gdelt_company", M.GDELT_DOC, ("timelinevolraw",), tmp_path, time.time() + 60, None)
    assert left == 1 and calls.count('"Throttled"') == 1           # one request, not 1 + 10 yearly ones
    st = M.Store(tmp_path / "gdelt_company_timelinevolraw.parquet")
    assert not st.has("THR") and st.has("X") and st.has("OK")
