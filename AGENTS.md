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

## AI experiment campaigns

When automated research is introduced later:

- Every experiment gets a unique ID.
- Record the parent experiment, hypothesis, changes, rationale, parameters, dataset access, result and decision.
- An agent must explain why the next experiment follows from prior evidence.
- Do not perform random indicator stacking or unrestricted parameter search.
- Enforce experiment budgets and sealed-test access controls.

## Live trading

Do not add or enable live-trading logic by default. Any future live deployment must include explicit risk limits, monitoring, failure handling, reconciliation and a deliberately small initial capital allocation.
