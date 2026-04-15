# LOGRE (LOcal GRaph Editor)

Logre is an open-source UI that helps you visualize, edit, and explore RDF graph data through SPARQL endpoints.

> Logre does not embed its own triple store. You can connect Logre to your own endpoint, or run it with the bundled RDF4J stack in containers.

Supported SPARQL endpoint technologies:

- Apache Jena Fuseki
- Eclipse RDF4J
- AllegroGraph
- Ontotext GraphDB

---

## Stack overview (container mode)

| Service | Purpose | Default port(s) |
|----|----|----|
| `logre` | Streamlit-based UI served by this repository | `8501` (`LOGRE_PORT`) |
| `rdf4j` | Official `rdf4j` image (Server + Workbench) | `8080` (`RDF4J_SERVER_PORT`) |

Both services run under the `dev` Docker Compose profile and persist their state in volumes (`logre_data`, `rdf4j_data`).

---

## Requirements

- A way to obtain the source code:
  - Git (recommended), or
  - Downloading the repository ZIP archive from GitHub.
- For `make start`: Linux/macOS shell (or WSL), `make`, Python 3 with `venv`, `git`, `curl`.
- For Docker/Podman mode: Docker Desktop or Docker Engine + Compose plugin (Podman + `podman compose` also works).
- For plain Python mode: Python 3.11+ and `pip`.

---

## Run Logre (3 ways)

### 1) `make start` (historical workflow)

From repository root:

```bash
make start
```

This will switch to `main`, update from git, install dependencies in `pipenv_logre`, and run Streamlit.

Useful variants:

- `make start-dev`
- `make reinstall`
- `make help`

---

### 2) Docker / Podman (recommended for turnkey setup)

From repository root:

```bash
docker compose --profile dev up --build
```

Podman equivalent:

```bash
podman compose --profile dev up --build
```

If you need a full rebuild without cache:

```bash
docker compose --profile dev build --no-cache
docker compose --profile dev up
```

Open:

- Logre UI: `http://localhost:8501` (or custom `LOGRE_PORT`)
- RDF4J Server API: `http://localhost:8080/rdf4j-server`
- RDF4J Workbench UI: `http://localhost:8080/rdf4j-workbench/repositories`
- Default repository endpoint: `http://localhost:8080/rdf4j-server/repositories/logre`

Optional port override:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
LOGRE_PORT=8502
RDF4J_SERVER_PORT=8081
```

RDF4J Workbench note:

Even if you expose RDF4J on another host port, Workbench connects to the internal URL `http://rdf4j:8080/rdf4j-server`.
In a fresh browser session, enter this URL when prompted, then go to **Repositories -> logre -> Use**.

Common commands:

- Start detached: `docker compose --profile dev up -d`
- Stop stack: `docker compose --profile dev down`
- Tail logs: `docker compose --profile dev logs -f logre`
- Rebuild without cache: `docker compose --profile dev build --no-cache`
- Reset everything (delete persisted data): `docker compose --profile dev down -v`

---

### 3) Plain Python (manual local run)

From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run src/server.py
```

Then open `http://localhost:8501`.

When the Model page is opened, Logre auto-downloads `src/lib/shacl-maker.js` if it is missing.

---

## Configuration & secrets

Logre stores its user configuration in a YAML file. If no config is present, Logre creates one from the bundled template.

Default locations (by OS):

- Linux: `~/.config/logre/logre-config.yaml`
- macOS: `~/Library/Application Support/Logre/logre-config.yaml`
- Windows: `%APPDATA%\Logre\logre-config.yaml`

Overrides (highest priority wins):

1. `LOGRE_CONFIG_PATH` (explicit file path)
2. `LOGRE_CONFIG_HOME` (directory override)
3. OS default locations above

Secrets should live in environment variables (or `.env` locally) and be referenced from the config with placeholders:

```yaml
endpoints:
  - name: my-endpoint
    technology: RDF4J
    url: ${LOGRE_SPARQL_URL}
    username: ${LOGRE_SPARQL_USERNAME}
    password: ${LOGRE_SPARQL_PASSWORD}
```

Example `.env` (local, not committed):

```bash
LOGRE_SPARQL_URL=https://example.org/rdf4j-server/repositories/myrepo
LOGRE_SPARQL_USERNAME=admin
LOGRE_SPARQL_PASSWORD=secret
```

Docker specifics:

- `LOGRE_CONFIG_PATH` is set to `/data/logre-config.yaml` (persistent volume).
- The config is templated from `docker/logre-config.yml` on first run only.
- Data graph autoconfiguration runs automatically in Docker; in local runs it is opt-in via `LOGRE_AUTOCONFIGURE_GRAPH=1`.

Configuration migrations run automatically when the format changes.

---

## License & documentation

Logre is released under the MIT License (see `LICENSE`).

- FAQ: `documentation/faq.md`
- Tests and QA notes: `tests.md`, `things_to_test.md`
