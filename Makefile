PY_SRCS=src
RADON_MIN_MI=65

.PHONY: help lint fmt type security cc mi hal raw check

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
	@echo "  check    - запуск всех проверок"

lint:
	poetry run ruff check $(PY_SRCS) --fix

fmt:
	poetry run ruff format $(PY_SRCS)

type:
	poetry run mypy $(PY_SRCS)

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

check: lint fmt type security cc mi hal raw