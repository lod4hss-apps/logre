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
	@echo "[make get-sdhss-shacls]: from Semantic-Data-for-Humanities/SDHSS-Profiles repository, put all Turtle file in the ontology folder"


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
	${PYTHON} -m pip install -r $(REQUIREMENTS_FILE) > /dev/null 2>&1
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
	$(PYTHON) -m streamlit run src/server.py


start-verbose: update-verbose install-verbose
	@echo "[makefile] Selecting environment $(PIPENV_NAME)..."
	@source $(PIPENV_NAME)/bin/activate && \
	cd src; pipenv run $(PYTHON) -m streamlit run server.py


get-sdhss-shacls-sparse: 
	@rm -rf ./SDHSS-Profiles
	@mkdir -p ontologies
	@git clone --depth 1 --filter=blob:none --sparse https://github.com/Semantic-Data-for-Humanities/SDHSS-Profiles.git
	@cd SDHSS-Profiles && git sparse-checkout set sdhss_shacl_profiles
	@mv SDHSS-Profiles/sdhss_shacl_profiles/*.ttl ./ontologies
	@rm -rf ./SDHSS-Profiles

get-sdhss-shacls: 
	@rm -rf ./SDHSS-Profiles
	@mkdir -p ontologies
	@git clone https://github.com/Semantic-Data-for-Humanities/SDHSS-Profiles.git
	@mv SDHSS-Profiles/sdhss_shacl_profiles/*.ttl ./ontologies
	@rm -rf ./SDHSS-Profiles