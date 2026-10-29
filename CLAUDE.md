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

Docs site (`docs/` + `mkdocs.yml`, built by [Zensical](https://zensical.org/), the Material for MkDocs successor, from the `docs` dependency group — not part of `dev`):

```bash
uv run --group docs zensical serve            # live preview at http://localhost:8000
uv run --group docs zensical build --strict   # same command Read the Docs runs
```

## Architecture

- `aktools/main.py` — builds the `FastAPI` app, serves the homepage and `/version`, and mounts the `app_core` router under `/api`. `gunicorn aktools.main:app` / `uvicorn aktools.main:app` both target this `app`.
- `aktools/core/api.py` — the heart of the service. `/api/public/{item_id}` looks the interface up in `dir(ak)`, calls `getattr(ak, item_id)(**query_params)`, and serializes the DataFrame to JSON via `call_interface`. Also serves the PyScript pages (`/api/show`, `/api/show-temp/{interface}`).
- `aktools/cli.py` — the `python -m aktools` entry point (Typer). It launches `uvicorn aktools.main:app` as a subprocess; the command is passed as an argument list (not a shell string) so paths with spaces work.
- `aktools/datasets.py` — resolves bundled assets (HTML templates, favicon) via `importlib.resources`. These files ship inside the wheel; `[tool.setuptools.package-data]` in `pyproject.toml` controls what is included.
- `aktools/utils.py` — `get_latest_version()` queries PyPI for the newest AKShare/AKTools version shown on the homepage. Tests that render the homepage must stub this to stay offline.
- `src/app.py` — the Vercel entry point; it just re-exports `app`.
- `.readthedocs.yaml` — installs only the `docs` group with `uv sync --locked --only-group docs` and runs `zensical build --strict`. Its pinned `uv==` version must match `UV_VERSION` in `build.yml`.

## Conventions

- **Packaging metadata lives in `pyproject.toml`** (there is no `setup.py`). The version is read dynamically from `__version__` in `aktools/_version.py` (re-exported by `aktools/__init__.py`).
- **A release bumps three places that must agree**, enforced by `scripts/check_release.py` in the release workflow: the git tag (`vX.Y.Z`), `__version__` in `aktools/_version.py`, and a `X.Y.Z: ...` entry in `docs/aktools_version.md`. The version history lives only in `docs/aktools_version.md` — do not re-add a copy to the package.
- Releasing: push a `vX.Y.Z` tag; `release_and_deploy.yml` verifies metadata, builds, checks the artifacts, uploads to PyPI, then creates the GitHub release.
- **`aktools/assets/html/akscript.html` pins two versions that must move together**: the PyScript release in the `<script>`/`<link>` URLs, and the Pyodide version in the `interpreter` URL (which must equal that PyScript release's default Pyodide — find it in its release notes or `core.js`). The interpreter is deliberately pointed at `fastly.jsdelivr.net` because PyScript's default `cdn.jsdelivr.net` is blocked on most networks in China; `test_show_pyodide_avoids_blocked_cdn` guards this.
- Python 3.11+ only, matching current AKShare. Commit messages follow Conventional Commits (checked by the `commit-msg` hook). PRs target `main`.
