"""Consumer earnings study: release timing, outcomes and point-in-time features."""
import numpy as np
import pandas as pd

from qtrade.data.consumer import _earnings_rows, is_consumer
from qtrade.data import make_market
from qtrade.research import consumer_earnings as C

NY = "America/New_York"


def test_sec_parsing_and_consumer_codes():
    block = {"form": ["8-K", "10-Q", "8-K"], "items": ["2.02,9.01", "", "5.02"],
             "acceptanceDateTime": ["2020-05-05T16:05:00.000Z", "2020-05-06T10:00:00.000Z", "2020-06-01T12:00:00.000Z"],
             "filingDate": ["2020-05-05", "2020-05-06", "2020-06-01"]}
    rows = _earnings_rows("ABC", block)
    assert len(rows) == 1 and rows[0]["items"] == "2.02,9.01"
    assert is_consumer(5812) and is_consumer("5311") and not is_consumer(3674) and not is_consumer(None)


def _setup():
    md, _ = make_market(n_stocks=20, n_days=1500, seed=2, start="2015-01-02")
    t = md.tickers[3]
    d = md.dates[700]
    events = pd.DataFrame({"ticker": [t, t, t],
                           "accepted": [pd.Timestamp(d.date()).tz_localize(NY) + pd.Timedelta(hours=16, minutes=5),
                                        pd.Timestamp(md.dates[760].date()).tz_localize(NY) + pd.Timedelta(hours=7),
                                        pd.Timestamp(md.dates[800].date()).tz_localize(NY) + pd.Timedelta(hours=12)],
                           "session": ["after_close", "before_open", "during"]})
    profiles = pd.DataFrame({"ticker": [t], "consumer": [True]})
    return md, events, profiles


def test_entry_is_the_last_close_before_the_release():
    md, events, profiles = _setup()
    ev = C.build_events(md, events, profiles)
    assert len(ev) == 2                                    # the mid-session release is left out
    assert ev.loc[0, "entry"] == 700 and ev.loc[0, "exit"] == 701        # after the close: MOC that day
    assert ev.loc[1, "entry"] == 759 and ev.loc[1, "exit"] == 760        # before the open: MOC the day before
    out = C.outcomes(md, ev)
    j = ev.loc[0, "col"]
    raw = md.open.iat[701, j] / md.close.iat[700, j] - 1
    assert abs(out.loc[0, "ann_ret"] - raw) < 0.05        # market-relative version of close -> next open


def test_page_views_of_the_entry_day_are_not_used():
    md, events, profiles = _setup()
    ev = C.outcomes(md, C.build_events(md, events, profiles))
    t = ev.loc[0, "ticker"]
    idx = pd.date_range("2015-01-01", md.dates[-1], freq="D")
    views = pd.DataFrame({t: np.full(len(idx), 100.0)}, index=idx)
    base = C.features(md, ev, views, None)
    views.loc[views.index >= md.dates[700], t] = 1e6        # a spike from the entry day on
    after = C.features(md, ev, views, None)
    assert np.isclose(base.loc[0, "wiki_attention"], after.loc[0, "wiki_attention"])


def test_trends_windows_stitch_onto_one_scale():
    from qtrade.data.consumer import _stitch

    idx = pd.date_range("2016-01-03", periods=300, freq="W")
    true = pd.Series(np.linspace(10, 80, 300), index=idx)
    a, b = true.iloc[:150], true.iloc[100:] * 0.5          # second window on its own 0-100 scale
    s = _stitch([a, b])
    assert s.index.is_unique and len(s) == 300
    assert np.allclose(s.iloc[-50:], true.iloc[-50:], rtol=0.05)


def test_google_trends_is_incremental(tmp_path, monkeypatch):
    import sys
    import types

    from qtrade.data import consumer

    calls = []

    class FakeReq:
        def __init__(self, *a, **k):
            pass

        def build_payload(self, kw, timeframe, geo):
            self.kw = kw[0]
            calls.append(self.kw)

        def interest_over_time(self):
            if self.kw == "Nothing Co":
                return pd.DataFrame()
            idx = pd.date_range("2016-01-03", periods=260, freq="W")
            return pd.DataFrame({self.kw: np.arange(260) % 100 + 1.0}, index=idx)

    monkeypatch.setitem(sys.modules, "pytrends", types.ModuleType("pytrends"))
    monkeypatch.setitem(sys.modules, "pytrends.request", types.SimpleNamespace(TrendReq=FakeReq))
    monkeypatch.setattr(consumer.time, "sleep", lambda s: None)
    terms = {"AAA": "Aaa Stores", "BBB": "Nothing Co"}
    assert consumer.google_trends(terms, tmp_path, budget_min=0).empty      # cache only: no fetching
    df = consumer.google_trends(terms, tmp_path, budget_min=5, pause=0)
    assert list(df.columns) == ["AAA"]
    n = len(calls)
    again = consumer.google_trends(terms, tmp_path, budget_min=5, pause=0)  # both done: nothing re-fetched
    assert len(calls) == n and list(again.columns) == ["AAA"]


def test_sec_names_become_search_terms(tmp_path, monkeypatch):
    from qtrade.data import consumer, fundamentals

    monkeypatch.setattr(consumer, "wiki_titles", lambda root: pd.DataFrame({"ticker": ["WMT"], "title": ["Walmart"]}))

    class FakeSec:
        def get_json(self, url):
            return {"0": {"ticker": "COST", "title": "COSTCO WHOLESALE CORP /NEW", "cik_str": 1},
                    "1": {"ticker": "WMT", "title": "Walmart Inc.", "cik_str": 2}}

    monkeypatch.setattr(fundamentals, "SecClient", FakeSec)
    assert consumer.company_search_terms(["WMT", "COST", "ZZZ"], tmp_path) == {"WMT": "Walmart",
                                                                               "COST": "Costco Wholesale"}
