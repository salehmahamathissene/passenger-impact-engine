.PHONY: install lint test demo clean

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check . --fix

test:
	pytest -q

demo:
	pie run --config configs/demo.yml --out out

clean:
	rm -rf out
