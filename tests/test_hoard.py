"""Data hoard: one file per open source, market data only in an encrypted tar, failures isolated."""
import gzip
import json
from datetime import datetime, timezone

import pandas as pd

from qtrade.data import hoard as H

NOW = datetime(2026, 10, 22, 17, 30, tzinfo=timezone.utc)


def test_gdelt_summary_groups_by_country_and_root_code():
    rows = []
    for country, root, tone in [("US", "14", -5.0), ("US", "14", -3.0), ("CH", "04", 2.0)]:
        r = [None] * 61
        r[1], r[26], r[28], r[29], r[30], r[31], r[33], r[34], r[53] = 20261022, root + "1", root, 3, -2.0, 4, 2, tone, country
        rows.append(r)
    g = {(x["country"], x["root_code"]): x for x in H.gdelt_summary(pd.DataFrame(rows))}
    assert g[("US", "14")]["events"] == 2 and g[("US", "14")]["tone"] == -4.0 and g[("US", "14")]["mentions"] == 8
    assert g[("CH", "04")]["events"] == 1


def test_collect_writes_open_files_and_encrypts_market(tmp_path, monkeypatch):
    def boom(s, now):
        raise RuntimeError("down")

    monkeypatch.setattr(H, "OPEN", {"hackernews": lambda s, now: {"hits": [1]}, "weather": boom})
    monkeypatch.setattr(H, "OPEN_DAILY", {"wiki_top": lambda s, now: {"items": []}})
    monkeypatch.setattr(H, "MARKET", {"coinbase": lambda s, now: {"BTC-USD": {"price": "1"}}})
    monkeypatch.setattr(H, "MARKET_DAILY", {})
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    status = H.collect(tmp_path, daily=False, public_key="config/ledger_public_key.pem", now=NOW)
    assert status == {"hackernews": "ok", "weather": "failed: down", "coinbase": "ok"}
    hn = json.loads(gzip.decompress((tmp_path / "2026-10-22/hackernews/1730.json.gz").read_bytes()))
    assert hn["data"] == {"hits": [1]}
    assert not (tmp_path / "2026-10-22/wiki_top").exists()          # daily sources only with --daily
    files = {p.name for p in (tmp_path / "2026-10-22/market").iterdir()}
    assert files == {"1730.tar.enc", "1730.tar.key.enc"}             # never the plain tar
