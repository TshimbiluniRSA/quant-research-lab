# Quant Research Lab

A learning-first quantitative research platform for testing market hypotheses, validating strategies statistically, and eventually paper-trading or live-trading only strategies that survive rigorous testing.

## North star

> Build a system capable of rejecting bad trading ideas quickly.

The project repeatedly asks:

1. Is there a measurable market effect?
2. Can that effect be turned into a tradeable strategy after realistic costs?
3. Does it survive data it has never seen before?

## Project philosophy

This is not a "build a profitable bot" project. It is a reproducible research environment where notebooks, statistics, Jesse backtests, experiment tracking, and later AI-assisted research are used to test hypotheses systematically.

Research code and strategy code are intentionally separated. Notebooks are the research laboratory; Jesse is the strategy execution and backtesting engine.

## Roadmap

### V0.1 — Jesse mechanics
- Install Jesse
- Understand project structure
- Import market data
- Run example strategies
- Learn routes, candles, orders, entries, exits, position sizing, stops, take-profit, fees and backtest outputs

### V0.2 — Quant research foundation
- Build the pandas/Jupyter research environment
- Learn returns, rolling volatility, rolling windows and forward returns
- Inspect distributions and candle quality
- Create the hypothesis/experiment/report structure

### V0.3 — First hypothesis research
- Start with AAPL 1-hour data
- Research large-move continuation / mean-reversion behaviour
- Do notebook analysis before writing a strategy
- Write a research conclusion

### V0.4 — Hypothesis to Jesse strategy
- Implement the simplest strategy justified by the research
- Run baseline backtests
- Compare notebook expectations with actual execution
- Inspect trades and backtest metrics

### V0.5 — Validation framework
- Train / validation / sealed-test separation
- Parameter sensitivity
- Walk-forward testing
- Bootstrap and Monte Carlo analysis
- Market-regime analysis

### V0.6 — Multi-market research
- AAPL
- SPY
- QQQ
- Other equities
- Later, crypto markets such as BTC-USDT and ETH-USDT

### V0.7 — Experiment database
- PostgreSQL-backed experiment tracking
- Strategy versions and lineage
- Metrics and decisions

### V0.8 — AI research assistant
- LLM-assisted hypothesis generation
- Jesse MCP integration
- Controlled experiment campaigns
- Automated experiment reports

### V0.9 — Research dashboard
- FastAPI
- React + TypeScript
- Experiment explorer
- Equity curves, drawdowns and parameter views

### V1.0 — Paper trading
- Live market data
- Paper execution
- Monitoring and alerts

### V1.1 — Controlled live trading
Only after a strategy survives the required research, validation and paper-trading stages.

## Initial research question

A deliberately narrow first hypothesis:

> After unusually strong hourly price moves in AAPL, does price tend to continue moving in the same direction during the following 1–4 hours?

The goal is not to assume the answer. The goal is to measure it, test its statistical significance, and reject it if the evidence is weak.

## Repository structure

```text
quant-research-lab/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── .env.example
├── research/
│   ├── hypotheses/
│   ├── notebooks/
│   ├── experiments/
│   └── reports/
├── strategies/
│   ├── baseline/
│   ├── momentum/
│   ├── mean_reversion/
│   └── trend/
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── src/
│   ├── analytics/
│   ├── features/
│   ├── validation/
│   ├── risk/
│   └── utils/
└── tests/
```

## Research workflow

```text
Notebook research
      ↓
Understand market behaviour
      ↓
Write a falsifiable hypothesis
      ↓
Implement in Jesse
      ↓
Backtest with realistic costs
      ↓
Analyse results and individual trades
      ↓
Validate robustness
      ↓
Reject, revise, or promote to paper trading
```

## Status

Current focus: **V0.1 and V0.2 only**.

No live trading. No serious ML. No autonomous strategy generation until the manual research and validation workflow is understood first.
