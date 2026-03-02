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
	@echo "[make update]: Update the code base and run the update script"
	@echo "[make update-verbose]: Same as [make update], but with logs"
	@echo "[make install]: Prepare everything so that the tool can be used"
	@echo "[make install-verbose]: Same as [make install], but with logs"
	@echo "[make reinstall]: Delete environment and install dependencies"
	@echo "[make reinstall-verbose]: Same as [make reinstall], but with logs"
	@echo "[make start]: Update, install and start Logre (main branch)"
	@echo "[make start-verbose]: Same as [make start], but with logs"
	@echo "[make start-dev]: Launch Logre from the dev branch"
	@echo "[make start-dev-verbose]: Same as [make start-dev], but with logs"


# Update code base from GitHub (main branch)
update: 
	@echo "[LOGRE] Current version:" $$(cat ./VERSION)
	@echo "[LOGRE] Updating code base..."
	@git pull > /dev/null 2>&1
	@echo "[LOGRE] Now having version:" $$(cat ./VERSION)
	@echo "[LOGRE] Running update scripts..."
	@cd scripts; ${PYTHON} update.py

# Same as previous, but with logs
update-verbose: 
	echo "[LOGRE] Current version:" $$(cat ./VERSION)
	echo "[LOGRE] Updating code base..."
	git pull
	echo "[LOGRE] Now having version:" $$(cat ./VERSION)
	echo "[LOGRE] Running update scripts..."
	cd scripts; ${PYTHON} update.py


# Set the right virtual environment (or create it), and install dependencies from requirements.txt
# Also get other GitHub code
install:
	@echo "[LOGRE] Checking if environment $(PIPENV_NAME) exists..."
	@if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[LOGRE] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME) > /dev/null 2>&1; \
	fi
	@echo "[LOGRE] Installing pip requirements..." && \
	./${PIPENV_NAME}/bin/python -m pip install -r $(REQUIREMENTS_FILE) > /dev/null 2>&1
	@rm -f src/lib/shacl-maker.js
	@curl -sL https://raw.githubusercontent.com/gaetanmuck/shacl-maker/refs/heads/main/src/index.js | sed -n '\|// To not include|q;p' > src/lib/shacl-maker.js

# Same as previous, but with logs
install-verbose:
	echo "[LOGRE] Checking if environment $(PIPENV_NAME) exists..."
	if [ ! -d "$(PIPENV_NAME)" ]; then \
		echo "[LOGRE] Environment $(PIPENV_NAME) not found. Creating..."; \
		$(PYTHON) -m venv $(PIPENV_NAME); \
	fi
	echo "[LOGRE] Installing pip requirements..." && \
	./${PIPENV_NAME}/bin/python -m pip install -r $(REQUIREMENTS_FILE)
	rm -f src/lib/shacl-maker.js
	curl -sL https://raw.githubusercontent.com/gaetanmuck/shacl-maker/refs/heads/main/src/index.js | sed -n '\|// To not include|q;p' > src/lib/shacl-maker.js


# Prune currect venv, and reinstall it
reinstall:
	@echo "[LOGRE] Removing environment ${PIPENV_NAME}..."
	@rm -rf ./${PIPENV_NAME}
	@make install

# Same as previous, but with logs
reinstall-verbose:
	echo "[LOGRE] Removing environment ${PIPENV_NAME}..."
	rm -rf ./${PIPENV_NAME}
	make install-verbose


# Set main branch, update code base, install dependencies and launch the webserver (also open browser)
start: 
	@git switch main > /dev/null 2>&1
	@make update
	@make install
	@echo "[LOGRE] Starting server..."
	@./${PIPENV_NAME}/bin/python -m streamlit run src/server.py

# Same as previous, but with logs
start-verbose: 
	git switch main
	make update-verbose
	make install-verbose
	echo "[LOGRE] Starting server..."
	./${PIPENV_NAME}/bin/python -m streamlit run src/server.py


# Set dev branch, update code base, install dependencies and launch the webserver (also open browser)
start-dev: 
	@git switch dev > /dev/null 2>&1
	@make update
	@make install
	@echo "[LOGRE] Starting server (dev branch)..."
	@./${PIPENV_NAME}/bin/python -m streamlit run src/server.py

# Same as previous, but with logs
start-dev-verbose: 
	git switch dev
	make update-verbose
	make install-verbose
	echo "[LOGRE] Starting server (dev branch)..."
	./${PIPENV_NAME}/bin/python -m streamlit run src/server.py

build-app-macos:
	./${PIPENV_NAME}/bin/python -m pip install PyInstaller
	rm -rf ./dist; rm -rf ./dist
	./${PIPENV_NAME}/bin/python -m PyInstaller \
		--windowed \
		--add-data=.streamlit:.streamlit \
		--add-data=defaults:defaults \
		--add-data=documentation:documentation \
		--add-data=docker/logre-config.yml:docker \
		--add-data=src:src \
		--add-data=README.md:. \
		--add-data=VERSION:. \
		--collect-all streamlit \
		--collect-all graphly \
		--collect-all dotenv \
		--icon=icon.ico \
		logre-launcher.py
	rm -rf ./build logre-launcher.spec
	cp ./icon.ico ./dist/logre-launcher.app/Contents/Resources/
	./${PIPENV_NAME}/bin/python ./scripts/finder-icon.py
	touch ./dist/logre-launcher

build-app-linux:
	./${PIPENV_NAME}/bin/python -m pip install PyInstaller
	rm -rf ./dist; rm -rf ./dist
	./${PIPENV_NAME}/bin/python -m PyInstaller \
		--windowed \
		--add-data=.streamlit:.streamlit \
		--add-data=defaults:defaults \
		--add-data=documentation:documentation \
		--add-data=docker/logre-config.yml:docker \
		--add-data=src:src \
		--add-data=README.md:. \
		--add-data=VERSION:. \
		--collect-all streamlit \
		--collect-all graphly \
		--collect-all dotenv \
		--icon=icon.ico \
		logre-launcher.py
	rm -rf ./build logre-launcher.spec

build-app-windows:
	./${PIPENV_NAME}/bin/python -m pip install PyInstaller
	rm -rf ./dist; rm -rf ./dist
	./${PIPENV_NAME}/bin/python -m PyInstaller \
		--windowed \
		--add-data=.streamlit:.streamlit \
		--add-data=defaults:defaults \
		--add-data=documentation:documentation \
		--add-data=docker/logre-config.yml:docker \
		--add-data=src:src \
		--add-data=README.md:. \
		--add-data=VERSION:. \
		--collect-all streamlit \
		--collect-all graphly \
		--collect-all dotenv \
		--icon=icon.ico \
		logre-launcher.py
	rm -rf ./build logre-launcher.spec
