# LOGRE (LOcal GRaph Editor)

Logre is an open-source tool designed to interact with SPARQL endpoints. It offers a simple graphical interface for visualizing, editing, and exploring graph-based data.

> ⚠️ Logre is not a standalone application with built-in storage. It’s a client tool for working with existing graph technologies.

Supported SPARQL Endpoint Technologies:
- Apache Jena Fuseki
- AllegroGraph
- Ontotext GraphDB

## Prerequisites before using Logre efficiently

1. **Have a SPARQL endpoint:** Logre connects to external graph stores, you’ll need an instance of a supported SPARQL endpoint running.
2. **Have an ontology:** Even if possible without, Logre is designed to rely on a defined ontology that is specified with SHACL files 
3. **Install Logre locally:** Install Logre on your machine and start the application (see installation instructions below).


## Get Started: Installation

### Technical requirements

In order to install Logre locally, there are also some technical requirements:
- Have basic knowledge of terminal usage ([here is a basic tutorial](https://www.freecodecamp.org/news/command-line-for-beginners/))
- Have a recent Python installation (above 3.8) ([here is a Python installation tutorial](https://realpython.com/installing-python/))
- Have Git installed ([here is a Git installation tutorial](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
- Linux & macOS users: Have "make" installed:
    - For Linux: `sudo apt install make`
    - For macOS: `xcode-select --install`

### Install Logre locally

0. Open a terminal and navigate to the place where you want to install Logre
1. Download sources: `git clone https://github.com/lod4hss-apps/logre.git`
2. Navigate into sources: `cd logre`

3. 1. For Windows users: you can open the folder with the folder explorer, and simply double click on the file `logre.bat`, this will handle virtual environments, dependencies, updates, start Logre, and open it in a new tab in your favorite browser.

    2. For Linux/macOS users: run `make start` inside Logre folder, and it will handle virtual environments, dependencies, updates, start Logre, and open it in a new tab in your favorite browser. *This will use the command `python3`. If you need to specify another command for python (e.g. `python3.10`) you need to create an file called ".env" in logre folder with the following content:*

    ```text
    PYTHON=python3.10
    ```


### Installation troubleshooting

If for any reason, the 3rd step does not work for you, here is a manual instruction of what to do to install it "manually". If you are on Windows, in the following commands, replace `python3` by `py`

4. Create the virtual environment `python3 -m venv pipenv_logre`
5. Activate the virtual environment `source ./pipenv_logre/bin/activate`
6. Install dependencies `python3 -m pip install -r requirements.txt`


## Get Started: Updates

If you use the bat file (Windows) or the `make start` recipe (Linux, macOS), updates are automatically done when you start Logre, otherwise, you need to `git pull` the repo, and do the manual installation again (see *Installation troubleshooting* above).


## Get Started: Start Logre

- For Windows users: double click on "logre.bat" file
- For Linux and macOS users: run `make start`
- Manual start (after installation): `python3 -m streamlit run src/server.py`

---

## Run Logre & Fuseki with Docker Compose

The repository now ships a cross-platform Docker setup that bundles Logre with an Apache Jena Fuseki triple store. This is the quickest way to get both services running together on Linux, macOS, or Windows (Docker Desktop / Podman).

### Prerequisites

- Docker Engine with Compose plugin (Docker Desktop on macOS/Windows, Docker Engine + docker-compose-plugin on Linux).
- About 2 GB of free disk space for images and data volumes.

### Quick start

1. *(Optional)* copy `.env.example` to `.env` if you want to override defaults such as exposed ports or the dataset name.
2. Build and start both services (choose the command matching your runtime):
   ```bash
   docker compose --profile dev up --build
   ```
   ```bash
   podman compose --profile dev up --build
   ```
3. Open the app at [http://localhost:8501](http://localhost:8501). Fuseki is exposed at [http://localhost:3030](http://localhost:3030).

The `dev` profile defines two services:

- `logre`: Streamlit application served on port 8501 (config persisted in a named volume).
- `fuseki`: Apache Jena Fuseki (pulled from `docker.io/stain/jena-fuseki:latest`) with a persistent dataset stored in a named volume. The dataset defaults to `logre`, can be changed with `FUSEKI_DATASET`, and runs with update support so Logre can write data.

During startup the app waits for Fuseki to become reachable and, if no configuration exists yet, seeds one that targets the bundled Fuseki dataset. All data (Logre config and Fuseki TDB) is stored in Docker-managed volumes for portability across operating systems; no host bind mounts are required.

> Tip: Because the Fuseki image is referenced via its fully qualified Docker Hub path, Docker and Podman pull it automatically without authentication prompts or interactive registry selection.

> Note: The container disables git-based branch detection (`LOGRE_SKIP_BRANCH_DETECTION=1`) so the app runs happily without a working `.git` directory. Local dev environments keep their usual behavior.
Fuseki auto-creates the dataset at `/<FUSEKI_DATASET>` (exposing `/sparql`, `/update`, `/upload`, `/data`) and Logre regenerates its config to target `http://fuseki:3030/<FUSEKI_DATASET>/sparql`. Adjust `FUSEKI_DATASET`, `FUSEKI_ADMIN_PASSWORD`, `LOGRE_PORT`, and `FUSEKI_PORT` in `.env` when you need different defaults.
### Common tasks
- Stop the stack: `docker compose --profile dev down` *(or `podman compose --profile dev down`)*
- Rebuild after code changes: `docker compose --profile dev up --build` *(or `podman compose --profile dev up --build`)*
- Reset data: `docker compose --profile dev down -v` *(or `podman compose --profile dev down -v` to remove volumes)*
- Tune dataset/ports: set `FUSEKI_DATASET`, `FUSEKI_ADMIN_PASSWORD`, `LOGRE_PORT`, and/or `FUSEKI_PORT` in `.env`; set `LOGRE_FORCE_CONFIG=0` to keep manual edits to `/data/logre-config.yaml`.

> ℹ️ Compose targets multi-architecture base images (amd64 & arm64) and has been validated with Docker Desktop and Podman.

---

> A user FAQ is available once Logre has started on your computer
