# Run Logre with Docker or Podman

This mode runs a ready-to-use stack with:

- `logre` (UI)
- `rdf4j` (server + workbench)

## Requirements

- Docker Desktop or Docker Engine + Compose plugin
- Or Podman + `podman compose`

## Launch with Docker Compose

From the repository root:

```bash
docker compose --profile dev up --build
```

If you need a full rebuild without cache:

```bash
docker compose --profile dev build --no-cache
docker compose --profile dev up
```

Then open:

- Logre UI: `http://localhost:8501`
- RDF4J Server API: `http://localhost:8080/rdf4j-server`
- RDF4J Workbench: `http://localhost:8080/rdf4j-workbench/repositories`

## Launch with Podman Compose

```bash
podman compose --profile dev up --build
```

## Optional port override

If ports are already used:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
LOGRE_PORT=8502
RDF4J_SERVER_PORT=8081
```

## Common commands

- Start detached: `docker compose --profile dev up -d`
- Stop stack: `docker compose --profile dev down`
- Tail logs: `docker compose --profile dev logs -f logre`
- Rebuild without cache: `docker compose --profile dev build --no-cache`
- Reset everything (delete persisted volumes): `docker compose --profile dev down -v`
