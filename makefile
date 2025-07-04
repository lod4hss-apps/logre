-include .env
export

default: help

SHELL := /bin/bash
PYTHON ?= python3
PIPENV_NAME := pipenv_logre
REQUIREMENTS_FILE := requirements.txt


help:
	@echo "[make help]: Outputs this help"
	@echo "[make update]: Update the code base"
	@echo "[make update-verbose]: Update the code base (with full logs)"
	@echo "[make install]: Prepare everything so that the tool can be used"
	@echo "[make install-verbose]: Prepare everything so that the tool can be used (with full logs)"
	@echo "[make start]: Update, install and start Logre"
	@echo "[make start-verbose]: Update, install and start Logre (with full logs)"


update: 
	@echo "[LOGRE] Current version:" $$(cat VERSION)
	@echo "[LOGRE] Updating code base..."
	@branch=$$(git rev-parse --abbrev-ref HEAD); \
	git pull origin $$branch > /dev/null 2<&1
	@echo "[LOGRE] Now having version:" $$(cat ./VERSION)


update-verbose: 
	@echo "[LOGRE] Current version:" $$(cat VERSION)
	@echo "[LOGRE] Updating code base..."
	@git pull origin main 
	@echo "[LOGRE] Now having version:" $$(cat ./VERSION)


install:
	@echo "[LOGRE] Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[LOGRE] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME) > /dev/null 2>&1; \
	fi
	@echo "[LOGRE] Activating environment $(PIPENV_NAME)..."
	@source ./$(PIPENV_NAME)/bin/activate && \
	echo "[LOGRE] Installing requirements..." && \
	${PYTHON} -m pip install -r $(REQUIREMENTS_FILE) > /dev/null 2>&1


install-verbose:
	@echo "[LOGRE] Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[LOGRE] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME); \
	fi
	@echo "[LOGRE] Activating environment $(PIPENV_NAME)..."
	@source ./$(PIPENV_NAME)/bin/activate && \
	echo "[LOGRE] Installing requirements..." && \
	${PYTHON} -m pip install -r $(REQUIREMENTS_FILE)


start: update install
	@echo "[LOGRE] Starting server..."
	@$(PYTHON) -m streamlit run src/server.py


start-verbose: update-verbose install-verbose
	$(PYTHON) -m streamlit run src/server.py