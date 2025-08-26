
# Telecom Monitor

Proyecto de aprendizaje (Python + Java) para monitorizar servicios de telecom.
Fase 1: ingesta con Python y SQLite. Fase 2: API con Java.

## Requisitos
- Python 3.11+

## Desarrollo rápido
```bash
cd ingest-python
python3 -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -U pip
pip install pytest ruff black anyio httpx selectolax
pytest -q
Calidad
	•	Lint: ruff check .
	•	Formato: black .
