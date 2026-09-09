PYTHON := .venv/bin/python
PIP := .venv/bin/pip
JUPYTER := .venv/bin/jupyter

.PHONY: setup jesse-up jesse-down jesse-logs backtest notebook test lint typecheck check

setup:
	python3.12 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PYTHON) -m ipykernel install --sys-prefix --name quant-research-lab --display-name "Quant Research Lab"

jesse-up:
	@test -f .env || (echo "Copy .env.example to .env first."; exit 1)
	docker compose --env-file .env -f docker/docker-compose.yml up -d

jesse-down:
	docker compose --env-file .env -f docker/docker-compose.yml down

jesse-logs:
	docker compose --env-file .env -f docker/docker-compose.yml logs -f jesse

backtest: jesse-up
	@echo "Open http://localhost:9000, import candles, then use the Backtest page."

notebook:
	$(JUPYTER) lab

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests strategies

typecheck:
	$(PYTHON) -m mypy src

check: lint typecheck test
