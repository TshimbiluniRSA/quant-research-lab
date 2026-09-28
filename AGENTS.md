# AGENTS.md

This repository is a quantitative research laboratory. Agents must prioritize research integrity, reproducibility, and capital preservation over impressive backtests.

## Core rules

1. Never optimize against the final test dataset.
2. Every strategy must start from a falsifiable market hypothesis. Indicators are tools, not hypotheses.
3. A profitable backtest is not evidence by itself.
4. Include realistic transaction fees and slippage assumptions.
5. Prefer simple strategies before complex strategies.
6. Keep tunable parameters to roughly 3–5 initially unless there is a documented reason to exceed that.
7. Every experiment must be reproducible from recorded code, data range, parameters, assumptions and results.
8. Record failed experiments. Failed research is useful research.
9. Never modify a strategy after seeing final-test results without creating a new research version and treating the old final test as contaminated.
10. AI may propose hypotheses, write code, run experiments and analyse results, but AI cannot declare a strategy profitable or safe for live trading.
11. No live trading until a strategy has passed in-sample research, validation, out-of-sample testing, parameter sensitivity, walk-forward testing, Monte Carlo analysis and paper trading.
12. Risk management overrides strategy signals.
13. Capital preservation matters more than return maximisation.

## Core principles

These extend the core rules above with where and when each obligation applies.

1. **Falsifiability first** (extends rule 2). Write the hypothesis in `research/hypotheses/`
   *before* any data is touched. "Let's see what the data shows" is not a hypothesis.
2. **Split before analysis** (extends rules 1 and 9). Assign research/validation/final-test
   boundaries per `research/DATA_SPLITTING.md` before analysis begins. Once a strategy has been
   evaluated on final-test data it is **contaminated** for that version. No "just one more tweak."
3. **Costs are part of the result** (extends rule 4). No result may be called "profitable" until
   fees and (once modeled) slippage are included. A backtest without realistic costs is not a
   result.
4. **No trading approval by default** (extends rule 11). Nothing is cleared for paper or live
   trading without a completed report in `research/reports/` documenting hypothesis → backtest →
   cost-adjusted result → validation outcome.
5. **Scope discipline.** ML, LLM agents, and optimization are out of scope until the
   fundamentals stages below are complete. Adding them early defeats the purpose of the project.

## Research discipline

- Ask why an experiment exists before running it.
- Do not add indicators simply because a strategy is losing.
- Prefer parameter plateaus to isolated "magic" values.
- Inspect individual trades and return distributions, not only headline metrics.
- Avoid look-ahead bias, survivorship bias and data leakage.
- Treat repeated validation access as a source of overfitting.
- Keep the final test period sealed during strategy development.
- Clearly label assumptions, estimates and limitations.

## Learning-first rule

During V0.1–V0.5, manual understanding is a requirement. Do not automate away Jesse notebooks, statistical checks or trade inspection before the researcher understands what each step is doing.

## Learning roadmap

Stages are completed by the human researcher, in order. Agents must not skip a stage or declare
one complete; only the researcher can say an exit criterion has been met.

### Stage 1 — Market mechanics (hands-on, in-repo)

- Run a simple strategy (e.g. `MovingAverageCrossover`) on BTC-USDT.
- Read the raw trade log line by line: entry price, exit price, fee paid, slippage assumption,
  PnL calculation.
- **Exit criterion:** can explain, unaided, exactly how a single trade's PnL was computed, fees
  included.

### Stage 2 — Break it on purpose

- Rerun with fees set to 0% and observe the distortion.
- Rerun with unrealistically high fees and watch the strategy die.
- **Exit criterion:** intuitive (not just intellectual) grasp of why "profitable in backtest" ≠
  "profitable after costs."

### Stage 3 — Returns and volatility (V0.2 scope)

- Compute simple returns, log returns, and rolling volatility by hand in a notebook (not via an
  unfamiliar library call).
- Plot them; observe volatility clustering.
- **Exit criterion:** can explain why log returns are used for compounding, and why volatility
  isn't randomly distributed over time.

### Stage 4 — Write one hypothesis, properly

- Pick one specific, falsifiable idea (e.g. "returns show short-term mean reversion after a 2%+
  single-candle move on 1h BTC-USDT").
- Fill out `research/hypotheses/HYPOTHESIS_TEMPLATE.md` before touching data.
- Assign research/validation/final-test boundaries upfront, per `research/DATA_SPLITTING.md`.

### Stage 5 — Test it, cost-adjusted, and write the conclusion

- Backtest on research/training data only.
- Check against validation data.
- Write the report in `research/reports/` even if the result is null.
- **A documented null result is progress. An untested guess is not.**

### Stage 6 (future, gated) — Risk and position sizing

- Only after a validated edge exists: sizing (Kelly-adjacent), drawdown tolerance, correlation
  handling across strategies.

### Stage 7 (future, gated) — ML / LLM exploration

- Only after at least one full Stage 1–5 cycle has been completed and documented. First question
  at this stage: "would a better feature or a better cost model solve this instead of a bigger
  model?"

## Rules for AI agents

These apply to Claude Code and any other tool reading this file, in addition to the rules above.

- Do not write ML, optimization, parameter-search, paper-trading, or live-trading code unless
  explicitly asked, even if it would "naturally" extend current work.
- Do not skip or auto-complete a learning stage on the human's behalf. The point is for them to
  do the analysis, not just receive the output.
- If asked to re-tune a strategy after final-test results have been seen, flag the contamination
  rather than silently complying.
- Present no backtest result as meaningful without fees, and call out explicitly when slippage
  is not modeled.
- Prefer explaining *why* a number is what it is over just producing the number.

## AI experiment campaigns

When automated research is introduced later:

- Every experiment gets a unique ID.
- Record the parent experiment, hypothesis, changes, rationale, parameters, dataset access, result and decision.
- An agent must explain why the next experiment follows from prior evidence.
- Do not perform random indicator stacking or unrestricted parameter search.
- Enforce experiment budgets and sealed-test access controls.

## Live trading

Do not add or enable live-trading logic by default. Any future live deployment must include explicit risk limits, monitoring, failure handling, reconciliation and a deliberately small initial capital allocation.

## Jesse-specific rules for V0.1 and V0.2

- Preserve Jesse's native root-level `docker/`, `storage/`, and `strategies/` layout.
- Put each runnable Jesse strategy in `strategies/<ClassName>/__init__.py`.
- Treat the dashboard configuration, data source, date range, fee, slippage, exchange mode,
  leverage, and strategy commit as part of every reproducible run record.
- Jesse stores 1-minute candles and derives larger timeframes. Do not pass hourly candles to
  `jesse.research.backtest()` as though they were native 1-minute input.
- Use only documented Jesse candle columns: timestamp, open, close, high, low, volume.
- Keep research labels such as forward returns out of strategy inputs to prevent look-ahead.
- Do not assume equity support. Verify provider, license, timestamp semantics, adjustment rules,
  and Jesse compatibility before using AAPL or another stock.
- Do not enable or install the live-trading plugin during V0.1/V0.2.
- Learning strategies must be simple, commented, unoptimized, and explicitly described as
  educational examples rather than market-edge claims.

## Current status

Verified against the repository on 2026-09-28. Update this section when the facts change.

- **Strategies** (`strategies/`): four long-only, unoptimized learning examples:
  `BuyAndHoldBaseline`, `MovingAverageCrossover` (SMA 20/50), `RsiMeanReversion`
  (RSI 14, 30/50), `SimpleBreakout` (20-bar high / 10-bar low). None has been backtested in a
  recorded experiment.
- **Notebooks** (`research/notebooks/`): `000_jesse_data_basics.ipynb` is a complete starter
  that has never been run (no outputs); it expects `data/raw/candles.csv`, which does not exist
  yet. `001_first_market_hypothesis.ipynb` is a TODO skeleton for an AAPL hourly-continuation
  question whose data provider is unconfirmed.
- **Source and tests**: only `src/analytics/market_data.py` is implemented (OHLCV cleaning,
  simple/log/forward returns, rolling volatility), covered by 14 tests in
  `tests/test_market_data.py`. `simple_returns`, `log_returns`, and `forward_returns` require
  `freq` for timestamped series and measure horizons in time: a missing candle yields NaN rather
  than a return spanning the gap. `src/features`, `src/risk`, `src/utils`, and `src/validation` are
  empty placeholders. `make check` (ruff, mypy, pytest) passes locally.
- **Templates**: `research/hypotheses/HYPOTHESIS_TEMPLATE.md`,
  `research/experiments/EXPERIMENT_TEMPLATE.md` (multi-run research experiment),
  `research/experiments/TEMPLATE.md` (single backtest run record, Stage 1–2), and
  `research/reports/REPORT_TEMPLATE.md`.
- **Research records**: no hypotheses written, no experiments recorded, and one report
  (`AAPL_HOURLY_ANCHOR_TREND_REVIEW.md`, a code review of an external strategy, not a result).
  Markdown run records in `research/experiments/` are tracked by Git; other files there and
  `research/experiments/generated/` are ignored.
- **Data split**: BTC-USDT boundaries declared in `research/DATA_SPLITTING.md` (Binance Spot;
  half-open UTC intervals): research [2019-01-01, 2024-01-01), validation [2024-01-01,
  2025-01-01), final test [2025-01-01, 2026-07-01) sealed for BTC on any exchange, 2026-07-01
  onward reserved. One split shared by all BTC-USDT hypotheses; the final-test access log is
  empty (never opened). No candles have been committed or checked into `data/`.
- **Roadmap progress**: Stage 1 not yet completed. No stage has been signed off by the
  researcher.
- **Known gaps**: slippage is **not modeled**. Address it before trusting any result on
  less-liquid instruments. No CI is configured (`make check` is local only). Equity data (e.g.
  AAPL) is intentionally not integrated; do not substitute crypto data for it.
