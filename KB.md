# Logre Technical Knowledge Base

## 1. Purpose and Scope
Logre is a Streamlit-based client that connects to existing SPARQL endpoints (Jena Fuseki, RDF4J, AllegroGraph, GraphDB) to inspect, edit, and visualize RDF knowledge. This document summarizes the repository structure, runtime architecture, recommended workflow, and the main features so team members can reason about the codebase quickly and extend it safely.

## 2. Repository Structure

| Path | Notes |
| --- | --- |
| `src/` | Streamlit app. See subdirectories below. |
| `src/pages/` | Each `.py` file is a routed page (Entity card, Data table, SPARQL editor, etc.). `server.py` redirects to the default documentation page if there is no configured data bundles (and none selected as default ones) or to the bundle overview. |
| `src/components/` | Cross-page helpers. `init.py` bootstraps Streamlit, loads config, and synchronizes query params; `menu.py` renders the sidebar, handles data bundle switching, and exposes quick actions (find/create entity). |
| `src/dialogs/` | Streamlit dialog fragments used from multiple pages (entity creation, editing, triple info, confirmations, saved-query naming, etc.). |
| `src/lib/` | Application state & utility layer. `state.py` is the central store that abstracts config files, Streamlit session state, toast notifications, pagination offsets, and cached SPARQL metadata. |
| `src/schema/` | Domain objects describing data bundles, model frameworks, SPARQL technology adapters, and error helpers. `data_bundle.py` defines how each bundle connects to a SPARQL backend and provides higher-level queries (find entities, fetch statements, run SPARQL). |
| `docker/`, `docker-compose.yml`, `Dockerfile` | Containerized stack bundling Logre with RDF4J. The `dev` profile spins up both UI and RDF4J server with persistent volumes and optional auto-bootstrap of repositories/config. |
| `scripts/` | Automation helpers (`bootstrap-rdf4j.sh`, `wait-for-http.sh`, `update.py`). |
| `logre-config.yaml`, `.env` | User-editable configuration defining prefixes, data bundles, SPARQL queries, and runtime overrides. Secrets can be supplied via environment variables referenced in the YAML. |
| `examples/` | Sample RDF datasets (N-Quads/Turtle) useful for testing import/export flows. |
| `documentation/faq.md` | End-user FAQ surfaced inside the application documentation page. |

## 3. Architecture Overview

### Streamlit entrypoint
- `src/server.py` and every file under `src/pages/` are standard Streamlit pages. `server.py` handles the landing page
- Each page starts with `components.init.init(...)` to load environment variables, parse config, sync query parameters, configure the UI shell, and emit pending toasts before rendering content.
- The sidebar is injected by `components.menu.menu()` on most pages. It exposes navigation, data bundle selection, and contextual actions (find/create entity dialogs) that rely on the global state module.

### State, configuration, and persistence
- `lib/state.py` wraps Streamlit's `session_state`. It memoizes the application version (`VERSION` file), loads YAML configuration from `logre-config.yaml` (or the bundled template in `docker/logre-config.yml`), and writes updates back to disk when prefixes, bundles, or saved queries change.
- The config location is resolved via `LOGRE_CONFIG_PATH` (highest priority), `LOGRE_CONFIG_HOME`, or OS-specific defaults (Linux `~/.config/logre/`, macOS `~/Library/Application Support/Logre/`, Windows `%APPDATA%\Logre\`).
- Endpoint credentials and URLs may reference environment variables using `${VAR}` placeholders so secrets can live in `.env` or the environment.
- Configuration drives:
  - Prefix registry (`graphly.schema.Prefixes`) used to shorten/expand URIs.
  - Saved SPARQL endpoints (`graphly.schema.Sparql`)
  - Saved Data Bundles (`src.schema.DataBundle`)
  - Saved SPARQL queries shown in the editor.
- State also tracks UX concerns: pagination offsets, selected entity URI, query parameters, list of entities currently expanded in charts, toast notifications, and recent SPARQL execution IDs (so multiple submissions do not rerun automatically).

### Data access layer
- `schema/data_bundle.py` encapsulates each configured Data Bundles. It instantiates:
  - A SPARQL client (`graphly.schema.Sparql`) chosen via `schema/sparql_technologies.py` (one class per supported backend technology).
  - Three `graphly.schema.Graph` for data, model, and metadata named graphs.
  - A `graphly.schema.Model` instance chosen via `schema/model_framework.py` to interpret the ontology details (label, comment, type properties, domains, ranges, etc; one class for each supported ontology description technology).
- That class exposes higher-level methods consumed by pages: running raw SPARQL queries, finding entities (with pagination/filters), retrieving card properties, computing data tables, dumping/importing triples, replacing the model graph, etc. All write operations (insert/delete) are scoped to a named graph argument so the UI can edit model metadata without touching data graphs.

### Dialog and workflow helpers
- Dialog modules under `src/dialogs` wrap confirmation prompts, find/create entity flows, triple inspectors, entity edits, and query naming. These functions are triggered via sidebar buttons or inline actions across pages, enabling cross-page reuse and centralized validation logic.

## 4. Intended Workflow

1. **Install & run the UI**
   - Local dev: clone the repo, optionally create `.env` to point `make start` at a specific Python executable, then run `logre.bat` (Windows) or `make start` (macOS/Linux). Logre bootstraps a virtualenv, installs requirements, applies updates, and launches Streamlit.
   - Containerized stack: run `docker compose --profile dev up` (or `podman compose --profile dev up`). This starts the Streamlit UI plus an RDF4J Server + Workbench, provisions a repository (unless `RDF4J_BOOTSTRAP_REPOSITORY=0`), and pre-loads a Logre configuration pointing at that endpoint.

2. **Configure connectivity**
   - Use the **Configuration** page to define prefixes and one or more data bundles. Each bundle collects endpoint technology, URL, credentials, base URI, model framework, and named graph URIs. The default bundle is auto-selected on load; users can switch bundles via the sidebar select box, which persists across pages thanks to `state.set_data_bundle`.
   - Saved SPARQL queries are stored inside the configuration file, so exporting/importing `logre-config.yaml` can share curated queries with the team, or simply re-execute specific queries.

3. **Import or seed data (optional)**
   - The **Import/Export** page supports uploading Turtle files into the data/model/metadata graphs or streaming entire `.nq` dumps through the SPARQL endpoint API. Model updates are handled by uploading SHACL Turtle files, after which Logre wipes the model graph and re-loads it.
   - Example datasets under `examples/` help validate that endpoints, SHACL shapes, and model-aware features (entity cards, charts) behave correctly before connecting to production data.

4. **Daily graph operations**
   - Select a bundle from the sidebar, then rely on the quick actions:
     - *Find entity* opens a dialog that hits `DataBundle.find_entities` with label/class filters, returning a paginated list to browse.
     - *Create entity* launches the entity creation dialog, using the model to list available classes, enforcing mandatory properties, and writing the resulting triples into the data graph.
   - Navigate to one of the entity-focused pages (Entity Card, Raw Triples, Visualization) or the Data Table view depending on the task.

5. **Iterate and analyze**
   - Users can run ad-hoc SPARQL queries, save favorites, export CSV results, and download chunks of the graph. The Statistics page provides quick sanity checks (class/property distribution) to validate data loads.
   - Editors can adjust prefixes, rename bundles, or mark a different bundle as default. Every change is persisted to `logre-config.yaml`, making the environment reproducible.

## 5. Main Functions & Pages

### Sidebar navigation
- Implemented in `src/components/menu.py`.
- Shows app version (read from `VERSION` via `state.get_version`), page links, the data bundle select box, and contextual buttons for finding/creating entities. When users switch bundles, the selection is stored in session state and the newly selected bundle's model is loaded via `DataBundle.load_model`.

### Configuration (`src/pages/configuration.py`)
- Two expanders manage **Prefixes** and **Data Bundles**.
- Prefixes rely on `graphly.schema.Prefix`; editing or deleting one writes back to disk via `state.update_prefix` which ultimately calls `state.save_config`.
- Data bundles can be added/edited via `dialogs.data_bundle_form`, set as default, or deleted (with confirmation). Each bundle persists with its friendly name, base URI, endpoint credentials, model framework, and graph URIs.
- The page links to documentation anchors so admins understand how prefixes and bundles influence the rest of the UI.

### Entity experiences
- **Entity Card** (`entity-card.py`): Central place to inspect an entity through the lens of the data model. Outgoing/incoming properties are fetched with pagination, and each section shows values, quick links, info dialogs, and per-property pagination. Buttons open the raw triple view, visualization, edit, or delete dialogs. Deleting removes all statements involving the entity (`data_bundle.delete('data', ...)`) and clears the entity from session state.
- **Raw Triples** (`entity-triples.py`): Displays basic statements (type, label, comment) plus all outgoing/incoming triples as clickable URIs. Useful when the card layout hides certain predicates or when debugging literal values.
- **Visualization** (`entity-chart.py`): Builds an interactive graph (PyVis/NetworkX) seeded with the current entity. Users can choose which properties to skip and expand nodes for incoming/outgoing paths. The chart automatically fetches additional statements through `state.entity_chart_*` helpers and shows per-node checkboxes to expand the graph further. Generated HTML is embedded directly in Streamlit.

### Data Table (`data-table.py`)
- Provides tabular browsing per class. Users select a class (excluding literal value classes), choose limit/sort/filter settings, and Logre fetches the result set via `DataBundle.get_data_table`. Each row links back to the Entity page. Pagination state persists per class URI (`state.data_table_get_page`).

### SPARQL Editor (`sparql-editor.py`)
- Code editor widget (via the `code_editor` component) with syntax highlighting and a Run button.
- Saved queries live in the configuration. Users pick one, edit it inline, run it, and optionally save a new version using `dialogs.query_name`.
- Results render as a DataFrame with CSV download if the endpoint returns tabular data; otherwise the raw payload (e.g., Turtle) is displayed. Non-select queries (INSERT/DELETE) trigger a toast.
- The UI tracks the last execution ID to prevent duplicate submissions when Streamlit reruns.

### Import / Export (`import-export.py`)
- **Import**: Upload `.nq` dumps directly to the endpoint or Turtle files into the selected named graph (data/model/metadata). Each destructive action is guarded by `dialogs.confirmation`.
- **Export**: Builds `.nq` dumps of the entire endpoint or Turtle dumps for individual graphs. The backend streams data through the SPARQL client before offering it as a download.
- **Update model**: Upload SHACL Turtle files, wipe the current model graph, and insert the new shapes. Includes warnings about shared graphs so users do not accidentally wipe data.

### Statistics (`statistics.py`)
- Uses quick SPARQL aggregate queries to compute class and property distributions. Results feed Plotly donut charts with consistent color palettes. This page doubles as a lightweight monitor to verify that imports produced the expected shape.

### Documentation page
- `pages/documentation.py` renders `documentation/faq.md` inside the app, so help content remains close to the UI. `server.py` redirects here by default to give new users context before touching data.

## 6. SHACL Interactions

- **Single source of model truth**: Every data bundle carries a SHACL (or compatible) model in the named graph referenced by `graph_model_uri`. When a bundle becomes active, `schema/data_bundle.py:42` loads the right model class via `schema/model_framework.py`, and `DataBundle.load_model()` fetches the shapes so the UI can reason about classes, properties, and constraints without repeated endpoint calls.
- **UI driven by shapes**: Entity Card layouts, creation/edit dialogs, charts, and data tables all ask the in-memory model which properties belong to a class, what ranges/domains they expect, and which literals are allowed. If a predicate is absent from the SHACL shapes it will not appear in those views even if triples exist, so keep the model graph in sync with production data.
- **Updating shapes**: The Import/Export page’s “Update model” flow uploads SHACL Turtle files, deletes the existing model graph, inserts the new shapes, and on the next rerun the model is reloaded automatically. Because the operation wipes the entire graph, ensure the model graph does not mix application data with shapes.
- **Validation expectations**: Logre does not execute SHACL validation reports; it relies on the backend SPARQL endpoint (or offline tooling) for enforcement. The app still prevents many mistakes by only exposing predicates/classes declared in the shapes and by prefilling domains/ranges when building triples.
- **Versioning guidance**: Store SHACL sources alongside application code or infrastructure definitions. When shapes change, re-run the “Update model” workflow in every environment and reload the app so cached models pick up the new definitions.

## 7. Automation, Ops, and Supporting Files

- **Docker stack**: `docker-compose.yml` defines the `logre` service (Streamlit app) and an `rdf4j` service. Environment variables (see `.env.example`) control exposed ports, repository names, whether to bootstrap RDF4J with `scripts/bootstrap-rdf4j.sh`, and whether Logre should seed a config targeting the bundled RDF4J instance. Logs show when the app is waiting for RDF4J (via `scripts/wait-for-http.sh`).
- **Makefile & scripts**: `make start` wraps environment bootstrap, dependency installation, auto-updates (`scripts/update.py`), and `streamlit run` invocation. Windows users rely on `logre.bat` for the same workflow.
- **Versioning**: The app displays the contents of `VERSION`. Release automation should bump this file before tagging so end-users know which version they run.
- **Testing/validation aids**: `things_to_test.md` lists manual QA scenarios; `examples/*.nq` provide sample data to load via Import/Export for smoke tests.

## 8. Extending Logre

- **New pages**: Add a file under `src/pages/` and optionally link it from the sidebar (`components/menu`). Import `components.init` and `components.menu`, then interact with `lib.state` and `schema.data_bundle` helpers instead of managing Streamlit session state manually.
- **Additional SPARQL backends**: Implement a new technology class in `schema/sparql_technologies.py`, ensuring it exposes the same API as existing ones (`run`, `upload_nquads`, etc.), then reference it from `DataBundle`.
- **Custom model frameworks**: Extend `schema/model_framework.py` if the ontology metadata is not SHACL-compatible. Ensure the resulting class provides `type_property`, `label_property`, `comment_property`, and `update`.
- **Dialogs & reusability**: Favor adding reusable dialogs under `src/dialogs/` rather than duplicating inline Streamlit widgets; share state through `lib.state` when cross-page coordination is required.

---
This document should evolve with the codebase. When adding new capabilities, update the relevant sections (structure, workflow, features) so engineers and technical writers have a single source of truth for how Logre is meant to operate.
