# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AKTools exposes [AKShare](https://github.com/akfamily/akshare)'s financial data interfaces as an HTTP API. It is a thin [FastAPI](https://fastapi.tiangolo.com/) layer: a request to `/api/public/<interface_name>` is translated into a call to the AKShare function of the same name, and the resulting `pandas.DataFrame` is returned as JSON. AKTools itself holds almost no business logic — nearly every data question is really an AKShare question.

## Common Commands

Development uses [uv](https://docs.astral.sh/uv/). `uv.lock` **is committed** and must stay resolved against official PyPI — `pyproject.toml` declares `[[tool.uv.index]]` for exactly this reason, so contributors behind a China mirror need no local changes. If a lock diff shows a mirror hostname, regenerate it with `uv lock`.

```bash
uv sync                        # dev is a PEP 735 default group — installs pytest, ruff, pre-commit
uv run pre-commit install      # install the pre-commit and commit-msg hooks

uv run ruff format --check .   # exactly what CI's lint job runs — these two must pass
uv run ruff check .
uv run ruff format . && uv run ruff check . --fix   # local auto-fix variants

uv run pytest                  # unit tests (CLI, templates, release check) — no network needed
```

Run the server locally:

```bash
uv run python -m aktools --host 127.0.0.1 --port 8080   # then open http://127.0.0.1:8080/docs
```

Smoke-test an interface once the server is up:

```bash
curl "http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=000001"
```

## Architecture

- `aktools/main.py` — builds the `FastAPI` app, serves the homepage and `/version`, and mounts two routers: `app_core` under `/api` and `app_user_login` under `/auth`. `gunicorn aktools.main:app` / `uvicorn main:app` both target this `app`.
- `aktools/core/api.py` — the heart of the service. `/api/public/{item_id}` and `/api/private/{item_id}` look the interface up in `dir(ak)`, build the argument string from the query params, call the AKShare function, and serialize the DataFrame. Also serves the PyScript pages (`/api/show`, `/api/show-temp/{interface}`).
- `aktools/login/` — a demo OAuth2 flow guarding the `private` route; `fake_users_db` is hard-coded demo data, not a real user store.
- `aktools/cli.py` — the `python -m aktools` entry point (Typer). It launches uvicorn as a subprocess; the command is passed as an argument list (not a shell string) so paths with spaces work.
- `aktools/datasets.py` — resolves bundled assets (HTML templates, favicon) via `importlib.resources`. These files ship inside the wheel; `[tool.setuptools.package-data]` in `pyproject.toml` controls what is included.
- `aktools/utils.py` — `get_latest_version()` queries PyPI for the newest AKShare/AKTools version shown on the homepage. Tests that render the homepage must stub this to stay offline.
- `src/app.py` — the Vercel entry point; it just re-exports `app`.

## Conventions

- **Packaging metadata lives in `pyproject.toml`** (there is no `setup.py`). The version is read dynamically from `__version__` in `aktools/__init__.py`.
- **A release bumps three places that must agree**, enforced by `scripts/check_release.py` in the release workflow: the git tag (`vX.Y.Z`), `__version__` in `aktools/__init__.py`, and a `X.Y.Z: ...` entry in `docs/aktools_version.md`. The version history lives only in `docs/aktools_version.md` — do not re-add a copy to `__init__.py`.
- Releasing: push a `vX.Y.Z` tag; `release_and_deploy.yml` verifies metadata, builds, checks the artifacts, uploads to PyPI, then creates the GitHub release.
- Python 3.11+ only, matching current AKShare. Commit messages follow Conventional Commits (checked by the `commit-msg` hook). PRs target `main`.
