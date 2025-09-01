-include .env # Read variable environment, needed if Python CLI command to use is different than "python3"
export # Make all variables available in the recipes (and sub-makes)

# By default, display all available commands
default: help

SHELL := /bin/bash
PYTHON ?= python3
PIPENV_NAME := pipenv_logre
REQUIREMENTS_FILE := requirements.txt


# Display all available commands. Is also the default ("make")
help:
	@echo "[make help]: Outputs this help"
	@echo "[make update]: Update the code base"
	@echo "[make update-verbose]: Update the code base (with full logs)"
	@echo "[make install]: Prepare everything so that the tool can be used"
	@echo "[make install-verbose]: Prepare everything so that the tool can be used (with full logs)"
	@echo "[make start]: Update, install and start Logre"
	@echo "[make start-verbose]: Update, install and start Logre (with full logs)"
	@echo "[make python-version]: Display what Python command version is set"

# Display python version
python-version:
	@echo "[LOGRE] Python command used: ${PYTHON}"

# Update code base from GitHub
update: 
	@echo "[LOGRE] Current version:" $$(cat VERSION)
	@echo "[LOGRE] Updating code base..."
	@branch=$$(git rev-parse --abbrev-ref HEAD); \
	git pull origin $$branch > /dev/null 2<&1
	@echo "[LOGRE] Now having version:" $$(cat ./VERSION)

#  Same as previous, but with git logs
update-verbose: 
	echo "[LOGRE] Current version:" $$(cat VERSION)
	echo "[LOGRE] Updating code base..."
	git pull origin main 
	echo "[LOGRE] Now having version:" $$(cat ./VERSION)


# Set the right virtual environment (or create it), and install dependencies from requirements.txt
install:
	@echo "[LOGRE] Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[LOGRE] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME) > /dev/null 2>&1; \
	fi
	@echo "[LOGRE] Installing requirements..." && \
	./${PIPENV_NAME}/bin/python -m pip install -r $(REQUIREMENTS_FILE) > /dev/null 2>&1

# Same as previous, but with venv logs, and install logs
install-verbose:
	echo "[LOGRE] Checking if environment $(PIPENV_NAME) exists..."
	if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[LOGRE] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME); \
	fi
	echo "[LOGRE] Installing requirements..." && \
	./${PIPENV_NAME}/bin/python -m pip install -r $(REQUIREMENTS_FILE)


# Update code base, install dependencies and launch the webserver (also open browser)
start: update install
	@echo "[LOGRE] Starting server..."
	@./${PIPENV_NAME}/bin/python -m streamlit run src/server.py

# Same as previous, but with update logs and install logs
start-verbose: python-version update-verbose install-verbose
	./${PIPENV_NAME}/bin/python -m streamlit run src/server.py