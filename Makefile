test:
	@pytest -q

lint:
	@pre-commit run --all-files

install:
	@pip-sync requirements.txt requirements_dev.txt

lock:
	@pip-compile --generate-hashes
	@pip-compile --generate-hashes requirements_dev.in
