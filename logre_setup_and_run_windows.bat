@echo off
SET REPO_URL=https://github.com/geovistory/logre.git
SET REPO_FOLDER=logre

REM Verifier si Python est installe
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Rendez-vous sur https://www.python.org/downloads/ pour l'installer.
    pause
    goto end
)

REM Verifier si Git est installe
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Git n'est pas installe ou pas dans le PATH.
    echo Rendez-vous sur https://git-scm.com/ pour l'installer.
    pause
    goto end
)

REM Cloner le depot s'il n'existe pas, sinon mettre a jour
if not exist "%REPO_FOLDER%\" (
    echo Clonage du depot depuis %REPO_URL% ...
    git clone %REPO_URL%
) else (
    echo Le dossier %REPO_FOLDER% existe deja. Mise a jour...
    cd %REPO_FOLDER%
    git pull
    cd ..
)

REM Aller dans le dossier clone
cd %REPO_FOLDER%

REM Creer l'environnement virtuel s'il n'existe pas
if not exist "pipenv_logre\Scripts\activate.bat" (
    echo Creation de l'environnement virtuel...
    python -m venv pipenv_logre
)

REM Activer l'environnement
echo Activation de l'environnement virtuel...
call pipenv_logre\Scripts\activate.bat

REM Installer les dependances
echo Installation des dependances...
pip install -r requirements.txt

REM Lancer Streamlit
echo Lancement de Streamlit...
python -m streamlit run src\server.py

REM Ouvrir le navigateur
start http://localhost:8501

:end