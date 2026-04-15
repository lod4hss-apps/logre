# Run Logre with Python

This mode runs Logre directly with a local Python environment.

## Requirements

- Python 3.11+
- `pip`

## Setup and launch

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run src/server.py
```

Then open `http://localhost:8501`.

## Notes

- This mode does not start a triple store.
- Add your SPARQL endpoint in Logre configuration.
- On first access to the Model page, Logre auto-downloads `shacl-maker.js` if missing.
- If you prefer the project-maintained scripted flow, use `make start` instead.
