# LOGRE (LOcal GRaph Editor)

Logre is an open-source UI that helps you visualize, edit, and explore RDF graph data through SPARQL endpoints. The repository now ships with a self-contained Docker stack so you can run Logre alongside a ready-to-use RDF4J server in seconds.

> ⚠️ Logre does not embed its own triple store. The Docker setup simply bundles the application with an RDF4J server so you start with a working endpoint out of the box.

Supported SPARQL endpoint technologies:

* Apache Jena Fuseki
* Eclipse RDF4J
* AllegroGraph
* Ontotext GraphDB


---

## Stack overview

| Service | Purpose | Default port(s) |
|----|----|----|
| `logre` | Streamlit-based UI served by this repository | `8501` (`LOGRE_PORT`) |
| `rdf4j` | Official `rdf4j` image (Server + Workbench) | `8080` (`RDF4J_SERVER_PORT`) for the REST API |

Both services run under the `dev` Docker Compose profile and persist their state in Docker-managed volumes (`logre_data`, `rdf4j_data`).


---

## Requirements

* Docker Desktop on macOS/Windows or Docker Engine + Compose plugin on Linux (Podman + `podman compose` also works).
* A way to obtain the source code:
  * Git (recommended, to clone the repository), or
  * Downloading the repository as a ZIP archive from GitHub.
* \~2 GB of free disk space for images and volumes.


---

## Quick start (Docker Compose)


1. Obtain the source code:

   **With Git (recommended):**
   ```bash
   git clone https://github.com/lod4hss-apps/logre.git
   cd logre
   ```
   **Without Git:**

    * Download the ZIP archive from GitHub

    * Extract it

    * Open a terminal in the extracted logre directory

      ### (Optional) Override default ports

      If the default ports are already in use on your system, you can override them.

      1.1. Copy the example environment file:
         ```bash
         cp .env.example .env
         ```

      1.2. Edit .env and adjust the ports:
         ```bash
         LOGRE_PORT=8502
         RDF4J_SERVER_PORT=8081
         ```

      > **RDF4J Workbench note:** The Workbench UI runs next to the RDF4J server inside the same container. Even if you expose the service on another host port via `RDF4J_SERVER_PORT`, the Workbench must always connect to the internal endpoint `http://rdf4j:8080/rdf4j-server`. When you open the Workbench in a new browser session (private window, fresh profile, cleared cookies), it will prompt you for the server URL: enter `http://rdf4j:8080/rdf4j-server`, click **Connect**, then go to **Repositories → logre → Use** before navigating to repository-specific pages.




2. Build the images (first time or after code changes):

   `docker compose --profile dev build`

   Podman users can run the same command with podman compose.
3. Run the stack:

   `docker compose --profile dev up`
4. Verify services operation:
   * Logre UI: [http://localhost:8501](http://localhost:8501/) (or your custom LOGRE_PORT)
   * RDF4J Server API: <http://localhost:8080/rdf4j-server>
   * RDF4J Workbench UI: [http://localhost:8080/rdf4j-workbench/repositories](http://localhost:8080/rdf4j-workbench/repositories/)
   * Default repository endpoint: http://localhost:8080/rdf4j-server/repositories/logre

The Logre container waits for RDF4J to become reachable, creates the repository named after RDF4J_REPOSITORY (defaults to logre), then seeds a configuration that directly targets it.


---

## Configuration & secrets

Logre stores its user configuration in a YAML file. If no config is present, Logre creates one from the bundled template.

Default locations (by OS):

* Linux: `~/.config/logre/logre-config.yaml`
* macOS: `~/Library/Application Support/Logre/logre-config.yaml`
* Windows: `%APPDATA%\Logre\logre-config.yaml`

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

* `LOGRE_CONFIG_PATH` is set to `/data/logre-config.yaml` (persistent volume).
* The config is templated from `docker/logre-config.yml` on first run (or when `LOGRE_FORCE_CONFIG=1`).
* Data graph autoconfiguration runs automatically in Docker; in local runs it is opt-in via `LOGRE_AUTOCONFIGURE_GRAPH=1`.

Configuration migrations run automatically when the format changes.


---

## **Everyday commands**

* Start (foreground): docker compose --profile dev up
* Start (detached): docker compose --profile dev up -d
* Stop: docker compose --profile dev down
* Tail logs: docker compose --profile dev logs -f logre
* Rebuild after code changes: docker compose --profile dev build
* Reset everything (delete persisted data): docker compose --profile dev down -v


---

## **License & documentation**

Logre is released under the MIT License (see LICENSE). A built-in FAQ becomes available from within the Logre UI once the application is running.
