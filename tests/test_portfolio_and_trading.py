import pytest
import numpy as np

from qtrade.backtest.costs import half_spread, trade_cost
from qtrade.backtest.engine import run_backtest
from qtrade.backtest.metrics import deflated_sharpe, probabilistic_sharpe
from qtrade.config import Config
from qtrade.data.universe import parse_ishares_holdings, share_class_variants
from qtrade.features.context import FeatureContext
from qtrade.live.alpaca_trader import plan_orders
from qtrade.pipeline import forward_returns
from qtrade.portfolio.optimizer import construct


def _inputs(n=300, k=5, seed=0):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n), rng.uniform(0.01, 0.03, n), rng.standard_normal((n, k))


def test_portfolio_is_dollar_and_factor_neutral():
    cfg = Config()
    z, sig, B = _inputs()
    w, info = construct(z, sig, B, 0.02, cfg)
    assert abs(w.sum()) < 1e-3
    assert np.abs(B.T @ w).max() < 1e-2
    assert np.abs(w).max() <= cfg.portfolio.max_weight + 1e-9
    assert np.abs(w).sum() <= cfg.portfolio.max_gross + 1e-9
    assert np.corrcoef(w, z)[0, 1] > 0.3


def test_no_edge_means_no_positions():
    z, sig, B = _inputs()
    w, info = construct(z, sig, B, 0.0, Config())
    assert np.all(w == 0) and info.binding == "no_edge"


def test_no_trade_band_keeps_book_when_costs_dominate():
    cfg = Config()
    z, sig, B = _inputs()
    w_tgt, _ = construct(z, sig, B, 0.02, cfg)
    huge_cost = np.full(len(z), 1.0)
    w, _ = construct(z, sig, B, 0.02, cfg, w_cur=np.zeros(len(z)), tcost=huge_cost)
    assert np.abs(w).sum() < 1e-6          # never worth trading
    w2, _ = construct(z, sig, B, 0.02, cfg, w_cur=w_tgt, tcost=np.zeros(len(z)))
    np.testing.assert_allclose(w2, w_tgt, atol=1e-5)  # free trading -> target


def test_costs_scale_with_liquidity_and_size():
    cfg = Config()
    hs = half_spread(np.array([1e9, 50e6, 1e6]), cfg)
    assert hs[0] < hs[1] < hs[2]
    small = trade_cost(np.array([1e4]), np.array([1e8]), np.array([0.02]), cfg)[0] / 1e4
    big = trade_cost(np.array([1e7]), np.array([1e8]), np.array([0.02]), cfg)[0] / 1e7
    assert big > small


def test_backtest_flat_forecast_is_flat(market, cfg):
    md, _ = market
    ctx = FeatureContext(md, cfg)
    pred = np.where(ctx.tradable.to_numpy(), 0.0, np.nan)
    fwd = forward_returns(md, cfg.model.horizon).to_numpy()
    bt = run_backtest(ctx, pred, fwd, cfg, start=md.dates[400])
    assert np.abs(bt.returns).max() < 1e-12


def test_backtest_oracle_makes_money(market, cfg):
    """Sanity check of the accounting: knowing tomorrow's returns must pay."""
    md, _ = market
    ctx = FeatureContext(md, cfg)
    fwd = forward_returns(md, cfg.model.horizon).where(ctx.tradable).to_numpy()
    bt = run_backtest(ctx, fwd, fwd, cfg, start=md.dates[400])
    assert bt.returns.mean() > 0 and bt.daily["gross"].mean() > 0.1


def test_sharpe_statistics():
    rng = np.random.default_rng(0)
    import pandas as pd

    r = pd.Series(rng.normal(0.001, 0.01, 2000), index=pd.bdate_range("2010-01-01", periods=2000))
    assert probabilistic_sharpe(r) > 0.95
    assert deflated_sharpe(r, [0.1, 0.5, 1.0, 1.5, 2.0]) < probabilistic_sharpe(r)


def test_plan_orders_rules():
    prices = {"AAA": 100.0, "BBB": 50.0, "CCC": 10.0, "DDD": 20.0}
    targets = {"AAA": 0.10, "BBB": -0.05, "CCC": -0.02, "DDD": 0.0001}
    positions = {"AAA": 50, "CCC": 100, "EEE": 7}
    orders, tgt = plan_orders(targets, prices, 100_000, positions, shortable={"BBB"}, min_order_value=50)
    by = {o.symbol: o for o in orders}
    assert by["AAA"].side == "buy" and by["AAA"].qty == 50          # 50 -> 100 shares
    assert by["BBB"].side == "sell" and by["BBB"].qty == 100        # open short
    assert by["CCC"].side == "sell" and by["CCC"].qty == 100        # not shortable -> just close the long
    assert "DDD" not in by                                          # rounds to zero shares
    assert by["EEE"].reason.startswith("exit")                      # not in targets -> exit


def test_flip_is_split_across_days():
    orders, _ = plan_orders({"AAA": -0.1}, {"AAA": 100.0}, 100_000, {"AAA": 30})
    assert len(orders) == 1 and orders[0].qty == 30 and orders[0].reason == "close before flip"


def test_ishares_parser_and_share_classes():
    text = (
        'iShares Russell 3000 ETF\nFund Holdings as of,"Oct 17, 2026"\n\n'
        'Ticker,Name,Sector,Asset Class,Market Value,Weight (%)\n'
        'AAPL,APPLE INC,Information Technology,Equity,"4,000,000",6.1\n'
        'BRKB,BERKSHIRE HATHAWAY INC CLASS B,Financials,Equity,"1,500,000",1.6\n'
        'MSFT,MICROSOFT CORP,Information Technology,Equity,"5,000,000",6.5\n'
        'XTSLA,BLK CSH FND TREASURY SL AGENCY,Cash and/or Derivatives,Money Market,"10,000",0.1\n'
    )
    df = parse_ishares_holdings(text)
    assert df["ticker"].tolist() == ["MSFT", "AAPL", "BRKB"]
    assert "BRK-B" in share_class_variants("BRKB")


def test_small_account_mode_holds_whole_shares_in_few_names(market, cfg):
    import copy

    md, _ = market
    c = copy.deepcopy(cfg)
    c.portfolio.max_names, c.portfolio.whole_shares, c.costs.aum = 20, True, 10_000
    ctx = FeatureContext(md, c)
    fwd = forward_returns(md, c.model.horizon).where(ctx.tradable).to_numpy()
    bt = run_backtest(ctx, fwd, fwd, c, start=md.dates[400])
    day = bt.weights.index[len(bt.weights) // 2]
    w = bt.weights.loc[day]
    shares = w * bt.daily["equity"].loc[day] / md.close.loc[day]
    held = w != 0
    assert held.sum() > 5
    assert np.abs(shares[held] - np.round(shares[held])).max() < 1e-2  # weights are stored as float32
    assert bt.daily["long_names"].median() + bt.daily["short_names"].median() <= 2 * c.portfolio.max_names


def test_backup_scheduled_run_skips_when_already_traded(monkeypatch, tmp_path):
    import qtrade.live.alpaca_trader as lt
    from qtrade.config import Config

    class A:
        pass

    class Fake:
        def __init__(self, orders):
            self.orders = orders

        def get_account(self):
            a = A()
            a.equity = "100000"
            return a

        def get(self, path, data=None):
            if path == "/orders":
                assert data["status"] == "all" and "after" in data
                return self.orders
            return []

        def get_portfolio_history(self, req):
            h = A()
            h.equity = [100000.0]
            return h

    cfg = Config()
    cfg.live.log_dir = str(tmp_path)
    monkeypatch.setattr(lt, "_client", lambda: Fake([{"id": "x"}]))
    assert lt.run_paper(cfg, dry_run=False, once_per_day=True) == {"skipped": True}
    monkeypatch.setattr(lt, "_client", lambda: Fake([]))
    monkeypatch.setattr(lt, "load_universe", lambda d: (_ for _ in ()).throw(RuntimeError("reached model")))
    with pytest.raises(RuntimeError, match="reached model"):
        lt.run_paper(cfg, dry_run=False, once_per_day=True)


def test_unshortable_names_never_get_short_weights(market, cfg):
    import copy

    from qtrade.portfolio.decider import Decider

    md, _ = market
    c = copy.deepcopy(cfg)
    c.portfolio.max_names = 30
    ctx = FeatureContext(md, c)
    fwd = forward_returns(md, c.model.horizon).where(ctx.tradable).to_numpy()
    dec = Decider(ctx, fwd, fwd, c)
    t = 600
    no_short = np.zeros(len(md.tickers), dtype=bool)
    no_short[::2] = True                       # half the universe can't be borrowed
    d = dec.decide(t, np.zeros(len(md.tickers)), 10_000, no_short=no_short)
    w = d.weights
    assert (w[no_short] >= -1e-9).all()        # never short the unborrowable names
    assert (w < 0).sum() > 3 and (w > 0).sum() > 3
    assert abs(w.sum()) < 0.05 * np.abs(w).sum()   # still roughly dollar-neutral


def test_regime_ic_and_edge_scaling(market, cfg):
    """Exposure follows the expected edge: a regime where the forecast has
    worked gets a bigger book than one where it hasn't."""
    import copy

    import pandas as pd

    from qtrade.portfolio.decider import Decider

    md, _ = market
    ctx = FeatureContext(md, cfg)
    fwd = forward_returns(md, cfg.model.horizon).where(ctx.tradable).to_numpy()
    T = len(md.dates)
    reg = np.zeros((T, 2))
    reg[: T // 2, 0], reg[T // 2:, 1] = 1, 1
    ctx.regimes = pd.DataFrame(reg, index=md.dates)
    rng = np.random.default_rng(0)
    pred = np.where(np.isfinite(fwd), rng.standard_normal(fwd.shape), np.nan)
    pred[T // 2:] = np.where(np.isfinite(fwd[T // 2:]), fwd[T // 2:], np.nan)   # skill only in regime 1
    c = copy.deepcopy(cfg)
    c.portfolio.regime_ic, c.portfolio.edge_scaling = True, 0.05
    dec = Decider(ctx, pred, fwd, c)
    t_noise, t_skill = T // 2 - 10, T - 20
    assert dec.ic_estimate(t_skill) > 5 * dec.ic_estimate(t_noise)
    w_noise = dec.decide(t_noise, np.zeros(len(md.tickers)), 1e7).weights
    w_skill = dec.decide(t_skill, np.zeros(len(md.tickers)), 1e7).weights
    assert np.abs(w_skill).sum() > 2 * np.abs(w_noise).sum()
