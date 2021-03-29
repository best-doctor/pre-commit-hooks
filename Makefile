test:
	@pytest -q

lint:
	@pre-commit run --all-files

install:
	@pip-sync requirements.txt requirements_dev.txt

lock:
	@pip-compile --no-emit-index-url --generate-hashes
	@pip-compile --no-emit-index-url --generate-hashes requirements_dev.in

spelling:
	@rozental .
