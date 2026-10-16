.PHONY: test run

test:
	python -m unittest discover -s tests -p 'test_*.py'

run:
	python -m app.cli start
