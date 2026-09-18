PY_SRCS=src
PY_LINT_TARGETS=src tests
RADON_MIN_MI=65

.PHONY: help lint fmt type security cc mi hal raw test check

help:
	@echo "Доступные команды:"
	@echo "  lint     - проверка Ruff с автоисправлением"
	@echo "  fmt      - форматирование Ruff"
	@echo "  type     - проверка типов Mypy"
	@echo "  security - проверка безопасности Bandit"
	@echo "  cc       - цикломатическая сложность Radon"
	@echo "  mi       - индекс поддерживаемости Radon"
	@echo "  hal      - метрики Halstead"
	@echo "  raw      - количество строк кода"
	@echo "  test     - запуск тестов Pytest"
	@echo "  check    - запуск всех проверок"

lint:
	poetry run ruff check $(PY_LINT_TARGETS) --fix

fmt:
	poetry run ruff format $(PY_LINT_TARGETS)

type:
	poetry run mypy $(PY_LINT_TARGETS)

security:
	poetry run bandit -r $(PY_SRCS) -lll -x .venv,venv,build,dist,migrations,tests

cc:
	poetry run radon cc -s -a $(PY_SRCS)

mi:
	poetry run radon mi $(PY_SRCS)

hal:
	poetry run radon hal $(PY_SRCS)

raw:
	poetry run radon raw $(PY_SRCS)

test:
	poetry run pytest

check: lint fmt type security cc mi hal raw test