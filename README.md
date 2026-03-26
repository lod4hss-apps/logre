# LOGRE (LOcal GRaph Editor)

Logre is an open-source UI to visualize, edit, and explore RDF graph data through SPARQL endpoints.

Logre does not embed its own triple store. You can connect it to your own SPARQL endpoint, or use the container stack that bundles Logre with RDF4J.

Supported SPARQL endpoint technologies:

- Apache Jena Fuseki
- Eclipse RDF4J
- AllegroGraph
- Ontotext GraphDB

---

## Run Logre (3 ways)

Choose one launch mode:

1. `make start` workflow (install + update + run): `documentation/run-with-make.md`
2. Docker or Podman stack: `documentation/run-with-containers.md`
3. Plain Python/venv launch: `documentation/run-with-python.md`

---

## Configuration and secrets

Logre stores its user configuration in a YAML file. If no config is present, Logre creates one from a template.

Default config locations:

- Linux: `~/.config/logre/logre-config.yaml`
- macOS: `~/Library/Application Support/Logre/logre-config.yaml`
- Windows: `%APPDATA%\Logre\logre-config.yaml`

Overrides (highest priority first):

1. `LOGRE_CONFIG_PATH` (explicit file path)
2. `LOGRE_CONFIG_HOME` (directory override)
3. OS default locations

Use environment variables for secrets and reference them in config:

```yaml
endpoints:
  - name: my-endpoint
    technology: RDF4J
    url: ${LOGRE_SPARQL_URL}
    username: ${LOGRE_SPARQL_USERNAME}
    password: ${LOGRE_SPARQL_PASSWORD}
```

---

## Documentation

- FAQ: `documentation/faq.md`
- Tests and QA notes: `tests.md`, `things_to_test.md`

---

## License

Logre is released under the MIT License (see `LICENSE`).
