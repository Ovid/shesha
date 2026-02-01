.PHONY: install test lint typecheck format all

install:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check src tests

typecheck:
	mypy src/shesha

format:
	ruff format src tests
	ruff check --fix src tests

all: format lint typecheck test
