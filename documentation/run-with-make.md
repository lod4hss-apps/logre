# Run Logre with `make start`

This mode is the historical local workflow managed by `makefile`.

## Requirements

- Linux/macOS shell (or WSL on Windows)
- `make`
- Python 3 with `venv`
- `git`
- `curl`

## Launch

From the repository root:

```bash
make start
```

What this target does:

1. Switches to `main`
2. Pulls latest changes
3. Creates/updates local virtual environment (`pipenv_logre`)
4. Installs dependencies from `requirements.txt`
5. Starts Streamlit on `http://localhost:8501`

## Useful alternatives

- Start from `dev` branch: `make start-dev`
- Reinstall environment: `make reinstall`
- List commands: `make help`

## Notes

- This mode does not start a triple store.
- Configure your SPARQL endpoint in Logre after startup.
