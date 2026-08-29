PYTHON ?= python
.PHONY: setup data train serve demo test lint format monitor
setup:
	$(PYTHON) -m pip install -e ".[dev]"
data:
	$(PYTHON) -m risk_platform.cli generate --count 5000
train:
	$(PYTHON) -m risk_platform.cli train
serve:
	$(PYTHON) -m uvicorn risk_platform.inference.api:app --host 0.0.0.0 --port 8000
demo:
	$(PYTHON) scripts/run_demo.py
test:
	$(PYTHON) -m pytest --cov=risk_platform --cov-report=term-missing
lint:
	$(PYTHON) -m ruff check src tests scripts && $(PYTHON) -m mypy src
format:
	$(PYTHON) -m ruff format src tests scripts
monitor:
	$(PYTHON) -m risk_platform.cli drift

