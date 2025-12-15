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
| `rdf4j` | Official `eclipse/rdf4j-workbench` image (Server + Workbench) | `8080` (`RDF4J_SERVER_PORT`) for the REST API, `8081` (`RDF4J_WORKBENCH_PORT`) for the workbench UI |

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


