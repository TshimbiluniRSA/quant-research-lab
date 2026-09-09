# Quant Research Lab

A learning-first environment for testing falsifiable market hypotheses, understanding Jesse,
and rejecting weak trading ideas before capital is considered.

The project repeatedly asks:

1. Is there a measurable market effect?
2. Can it become a tradable strategy after realistic costs?
3. Does it survive genuinely unseen data?

A profitable backtest is not evidence by itself. No code in this repository is approved for
live trading.

## Current scope

- **V0.1 — Jesse mechanics:** project structure, candles, routes, orders, example strategies,
  fees, backtests, metrics, and trade inspection.
- **V0.2 — research foundation:** Jupyter, pandas, returns, rolling volatility, forward returns,
  data-quality checks, research templates, and utility tests.

AI agents, MCP automation, optimization campaigns, ML, APIs, dashboards, paper execution, and
live trading are deliberately out of scope.

## Verified Jesse setup

This setup was checked against Jesse's official documentation and release metadata on
2026-09-09:

- Jesse supports Python 3.10–3.13; this project uses Python 3.12.
- Docker is Jesse's recommended beginner setup because the application needs PostgreSQL and
  Redis. A native `pip install jesse` remains possible when those services are installed.
- The project template uses root-level `docker/`, `storage/`, and `strategies/`. This repository
  preserves those conventions instead of wrapping Jesse in a custom directory.
- Sensitive service configuration belongs in `.env`; application/backtest settings are managed
  in the dashboard.
- Jesse imports and stores 1-minute candles, then builds larger timeframes as needed.
- The dashboard creates strategies under `strategies/<Name>/__init__.py` and runs backtests after
  candles have been imported. The `jesse.research` API also supports notebook workflows.

References: [Getting Started](https://docs.jesse.trade/docs/getting-started/),
[Docker](https://docs.jesse.trade/docs/getting-started/docker),
[Configuration](https://docs.jesse.trade/docs/configuration),
[Importing Candles](https://docs.jesse.trade/docs/import-candles),
[Research API](https://docs.jesse.trade/docs/research/candles), and
[Backtesting](https://docs.jesse.trade/docs/backtest/).

### AAPL constraint

Jesse's current official
[supported backtest exchanges](https://docs.jesse.trade/docs/supported-exchanges/) are crypto
exchanges. No native AAPL/equity candle importer was verified. The first AAPL hypothesis
therefore remains data-source-neutral: do not choose dates or convert equity data for Jesse
until provider coverage, licensing, market-session semantics, corporate-action adjustment, and
required 1-minute history have been confirmed. BTC-USDT results cannot validate an AAPL
hypothesis.

## Prerequisites on Windows + WSL2

Develop inside the Linux filesystem in WSL, not under `/mnt/c`, to avoid slow file I/O and
permission surprises. Install:

- WSL2 with a current Ubuntu distribution
- Python 3.12 and its `venv` module
- Docker Desktop with WSL integration, or Docker Engine inside WSL
- GNU Make and Git

Confirm the tools from WSL:

```bash
python3.12 --version
docker --version
docker compose version
```

## Install the research environment

Dependencies have one declared source of truth: `pyproject.toml`. Jesse 3.0.7 is pinned, and
scientific-library constraints match that release.

```bash
make setup
```

This creates `.venv`, installs the project with development tools, and registers the
`Quant Research Lab` Jupyter kernel. Activate it manually when desired:

```bash
source .venv/bin/activate
```

## Start Jesse

Create a local configuration and change both placeholder passwords to the same strong local
values before the first start:

```bash
cp .env.example .env
make jesse-up
make jesse-logs
```

Open <http://localhost:9000>. The Compose stack uses the official Jesse 3.0.7 image plus local
PostgreSQL and Redis services. It intentionally runs `jesse run` without installing the live
plugin. Database files stay under ignored `docker/postgres-data/`. For optional host-side Jesse
research calls, Compose exposes PostgreSQL only on `127.0.0.1:5434` and Redis only on
`127.0.0.1:6380`, avoiding common local service ports.

Stop the stack with:

```bash
make jesse-down
```

## Import candles and run a sample backtest

1. Start Jesse and open its dashboard.
2. Open **Import Candles**.
3. For a small mechanical test, select a supported exchange such as `Binance Spot`, choose
   `BTC-USDT`, and choose a modest start date. Jesse imports through the present; availability
   depends on the exchange.
4. Open **Backtest**, create one route using `BTC-USDT`, `1h`, and one strategy from
   `strategies/`.
5. Choose only a range covered by imported candles. Configure an explicit starting balance and
   realistic fee. Record the missing slippage assumption as a limitation if the selected Jesse
   mode cannot model it directly.
6. Run the backtest, then inspect orders, individual trades, drawdown, return distributions, and
   benchmark—not only net profit or Sharpe ratio.

`make backtest` starts the stack and prints the dashboard reminder. Candle download and backtest
choices remain manual during the learning-first stages.

## Start Jupyter

```bash
make notebook
```

Begin with `research/notebooks/000_jesse_data_basics.ipynb`. It expects a small user-supplied CSV
at `data/raw/candles.csv` and explains the schema, or it can be adapted to candles already
imported into Jesse. Run its cells yourself and inspect every output.

`001_first_market_hypothesis.ipynb` is deliberately a skeleton. It contains no fabricated AAPL
data, date split, result, or conclusion.

## Quality commands

```bash
make test       # utility behavior
make lint       # source, tests, and learning strategies
make typecheck  # reusable source modules
make check      # all three
```

Do not unit test Jesse internals. The project tests only its own transparent transformations.
The test command disables unrelated third-party pytest plugins because Jesse 3.0.7 pins pytest
6.2 while newer packages in its runtime dependency set expose plugins for newer pytest releases.

## Repository structure

```text
quant-research-lab/
├── docker/                  # Jesse-native Compose stack
├── storage/                 # ignored Jesse runtime outputs
├── strategies/              # Jesse-native class-named strategy folders
├── research/
│   ├── hypotheses/          # falsifiable claims and template
│   ├── notebooks/           # manual, educational analysis
│   ├── experiments/         # reproducible run records
│   └── reports/             # conclusions, limitations, and reviews
├── data/                    # metadata plus ignored raw/processed data
├── src/                     # reusable analytics/features/validation/risk/utils
├── tests/                   # tests for our own code
├── pyproject.toml           # Python dependency source of truth
└── Makefile                 # readable local commands
```

## Data separation

The full policy is in [`research/DATA_SPLITTING.md`](research/DATA_SPLITTING.md).

- Research/training data is available during hypothesis development.
- Validation data is accessed sparingly for documented comparisons and robustness checks.
- Final-test data stays sealed until the hypothesis, implementation, parameters, costs, and
  decision criteria are frozen.

Never modify a strategy after seeing final-test results without creating a new research version
and marking the old final test contaminated for that version.

## Current status and next step

V0.1/V0.2 structure, commands, utilities, templates, notebook starters, and four small learning
strategies are present. The next manual milestone is intentionally modest: install the local
environment, start Jesse, import one supported dataset, inspect it in the first notebook, and run
one example backtest. Do not optimize the result.
