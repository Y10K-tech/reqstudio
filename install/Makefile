# Makefile for ReqStudio installation tasks (use: make -f install/Makefile <target>)

.PHONY: help unix-install unix-uninstall docker-build docker-run docs-server

help:
	@echo "Targets:"
	@echo "  unix-install    Install ReqStudio on Linux/macOS into .venv and create launcher"
	@echo "  unix-uninstall  Remove launcher and .venv"
	@echo "  docker-build    Build docs server image"
	@echo "  docker-run      Run docs server (port 8808)"
	@echo "  docs-server     Run FastAPI docs server locally (requires dependencies)"

unix-install:
	bash install/unix/install_reqstudio.sh

unix-uninstall:
	bash install/unix/uninstall_reqstudio.sh

docker-build:
	docker build -f install/docker/Dockerfile -t reqstudio-docs .

docker-run:
	docker run --rm -p 8808:8808 reqstudio-docs

docs-server:
	uvicorn api.docs_server:app --host 127.0.0.1 --port 8808
