# AKTools - Agent Guidance

## Quick Start

```bash
pip install -r requirements.txt
python -m aktools                    # CLI (default: http://127.0.0.1:8080)
python -m aktools --host 0.0.0.0 -P 9000  # custom bind
```

## Project Structure

- `aktools/` - main package
- `aktools/cli.py` - Typer CLI (entry point via `__main__.py`)
- `aktools/main.py` - FastAPI app setup (launched by CLI via uvicorn)
- `aktools/core/` - API route definitions
- `tests/` - pytest tests (currently minimal: `test_cli.py`, `test_demo.py`)
- `src/app.py` - additional source

## Dev Commands

```bash
ruff check .                    # lint (uses ruff, not flake8)
ruff format .                   # format
pytest                          # run tests
pre-commit install              # setup hooks (conventional commits + ruff)
```

## Tooling Notes

- **Linter/Formatter**: ruff (config in `pyproject.toml`, targets Python 3.12)
- **Pre-commit**: enforces conventional commits (`feat:`, `fix:`, etc.)
- **FastAPI docs**: auto-generated at `/docs` and `/redoc` when running
- **Build**: CI uses flake8 (legacy) but project standardized on ruff

## Gotchas

- `python -m aktools` runs CLI → launches uvicorn subprocess (not direct module run)
- `aktools/main.py` has `if __name__ == "__main__"` for direct uvicorn run, but CLI is preferred
- Package requires `akshare>=1.16.25` (large finance data dependency)
- Version derived from `aktools/__init__.py` via regex in `setup.py`
