default: help

SHELL := /bin/bash
PYTHON := python3.10
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
	@echo "[makefile] Current version:" $$(cat VERSION)
	@echo "[makefile] Updating code base..."
	@git pull origin main > /dev/null 2<&1
	@echo "[makefile] Now having version:" $$(cat ./VERSION)


update-verbose: 
	@echo "[makefile] Current version:" $$(cat VERSION)
	@echo "[makefile] Updating code base..."
	@git pull origin main 
	@echo "[makefile] Now having version:" $$(cat ./VERSION)


install:
	@echo "[makefile] Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[makefile] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME) > /dev/null 2>&1; \
	fi
	@echo "[makefile] Activating environment $(PIPENV_NAME)..."
	@source ./$(PIPENV_NAME)/bin/activate && \
	echo "[makefile] Installing packages from $(REQUIREMENTS_FILE)..." && \
	pip install -r $(REQUIREMENTS_FILE) > /dev/null 2>&1
	@echo "[makefile] Initializing folder..."
	@mkdir -p "./data"
	@touch "./data/saved_endpoints"
	@touch "./data/saved_queries"


install-verbose:
	@echo "[makefile] Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[makefile] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME); \
	fi
	@echo "[makefile] Activating environment $(PIPENV_NAME)..."
	@source ./$(PIPENV_NAME)/bin/activate && \
	echo "[makefile] Installing packages from $(REQUIREMENTS_FILE)..." && \
	pip install -r $(REQUIREMENTS_FILE)
	@echo "[makefile] Initializing folder..."
	@mkdir -p "./data"
	@touch "./data/saved_endpoints"
	@touch "./data/saved_queries"


start: update install
	@echo "[makefile] Selecting environment $(PIPENV_NAME)..."
	@source $(PIPENV_NAME)/bin/activate && \
	cd src; $(PYTHON) -m streamlit run server.py


start-verbose: update-verbose install-verbose
	@echo "[makefile] Selecting environment $(PIPENV_NAME)..."
	@source $(PIPENV_NAME)/bin/activate && \
	cd src; pipenv run $(PYTHON) -m streamlit run server.py