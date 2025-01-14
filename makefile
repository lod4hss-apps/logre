default: help

SHELL := /bin/bash
PIPENV_NAME := pipenv_logre
REQUIREMENTS_FILE := requirements.txt

help:
	@echo "[make help]: Outputs this help"
	@echo "[make install]: Prepare everything so that the tool can be used"
	@echo "[make start]: Launch Logre"
	@echo "[make update]: Update the code base"


# Recipe to create and activate the environment, then install packages
install:
	@echo "Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "Environment $(PIPENV_NAME) not found. Creating..."; \
		python3.10 -m venv $(PIPENV_NAME) > /dev/null 2>&1; \
	fi
	@echo "Activating environment $(PIPENV_NAME)..."
	@source ./$(PIPENV_NAME)/bin/activate && \
	echo "Installing packages from $(REQUIREMENTS_FILE)..." && \
	pip install -r $(REQUIREMENTS_FILE) > /dev/null 2>&1
	@echo "Initializing folder..."
	@mkdir -p "./data"
	@touch "./data/saved_endpoints"
	@touch "./data/saved_queries"

update: 
	@echo "Current version:" $$(cat VERSION)
	@echo "Updating code base..."
	@git pull origin main > /dev/null 2<&1
	@echo "Now having version:" $$(cat ./VERSION)

start: update install
	@echo "Selecting environment $(PIPENV_NAME)..."
	@source $(PIPENV_NAME)/bin/activate && \
	cd src; python3.10 -m streamlit run server.py
