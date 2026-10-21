.PHONY: up down pipeline logs ci venv
up:        ## pipeline + dashboard em container
	docker compose up --build -d
down:
	docker compose down
pipeline:  ## so o pipeline, local
	.venv/bin/python appleAnalisys.py
logs:
	docker compose logs --tail=80
ci:        ## mesma sequencia do CI, localmente (ver scripts/ci_local.sh)
	bash scripts/ci_local.sh
venv:
	python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
