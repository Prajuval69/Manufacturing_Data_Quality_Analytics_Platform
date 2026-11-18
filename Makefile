PYTHON ?= python
.PHONY: setup all test api
setup:
	$(PYTHON) -m pip install -r requirements.txt
all:
	$(PYTHON) -m src.cli all
test:
	$(PYTHON) -m pytest -q
api:
	$(PYTHON) -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
