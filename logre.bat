@echo off
SET REPO_URL=https://github.com/geovistory/logre.git
SET REPO_FOLDER=.
SET PIPENV_NAME=pipenv_logre
SET REQUIREMENTS_FILE=requirements.txt

REM [LOGRE] Check Python installation...
@where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    @echo "[ERROR] Python ('python') not found (installed or in PATH)."
    @echo "[ERROR] Go to https://www.python.org/downloads/ to install it."
    @pause
    @goto end
)

REM [LOGRE] Check Git installation...
@where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    @echo "[ERROR] Git ('git') not found (installed or in PATH)."
    @echo "[ERROR] Go to https://git-scm.com/ to install it."
    @pause
    @goto end
)

REM [LOGRE] Updating code base...
@git pull

REM [LOGRE] Create virtual environment...
if not exist "pipenv_logre\Scripts\activate.bat" (
    @python -m venv %PIPENV_NAME%
)

REM [LOGRE] Activate virtual environment...
call pipenv_logre\Scripts\activate.bat

REM [LOGRE] Installing dependencies...
@pip install -r %REQUIREMENTS_FILE%

REM [LOGRE Install GitHub Dependencies]
@git clone https://github.com/lod4hss-apps/graphly.git
@cd graphly; pip install .

REM [LOGRE] Starting Logre...
@python -m streamlit run src\server.py
@start http://localhost:8501

:end