test:
	@pytest -q

lint:
	@pre-commit run --all-files

install:
	@pdm sync --dev

lock:
	pip install pdm
	pdm lock --update-reuse
	$(MAKE) lock-export

lock-export:
	@pdm export -o requirements.txt --prod --no-extras
	@pdm export -o requirements_dev.txt -G dev --no-extras