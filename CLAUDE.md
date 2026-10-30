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

Docs pages follow a beginner learning path (`index.md` → `getting-started.md` → `guide/{usage,catalog,examples}.md` → `deploy.md` → `faq.md`). `--strict` fails on broken Markdown links and anchors. The MCP client config snippet (`uvx --from aktools aktools-mcp`) is repeated in `README.md`, `docs/index.md`, `docs/getting-started.md#mcp` and `docs/guide/mcp.md` — change all four together.

## Architecture

- `aktools/main.py` — builds the `FastAPI` app, serves the homepage and `/version`, and mounts the `app_core` router under `/api`. `gunicorn aktools.main:app` / `uvicorn aktools.main:app` both target this `app`.
- `aktools/core/api.py` — the HTTP routes only: `/api/public/{item_id}` (`call_interface` pops `_format`, calls `fetch_dataframe`, and builds the JSON or file response) and `/api/interfaces`.
- `aktools/core/fetch.py` — `fetch_dataframe`, the one code path that calls AKShare, shared by `/api/public` and the MCP `get_data` tool: checks `is_interface`, runs both caches, calls `getattr(ak, item_id)(**params)`, and maps failures to `InterfaceError(message, status_code)`. Importing it also applies the proxy/timeout settings, so stdio MCP gets them too.
- `aktools/core/formats.py` — DataFrame → JSON records, CSV or xlsx (`to_records`, `to_file_bytes`, `TooManyRowsError` for the Excel row limit).
- `aktools/core/log.py` — the `AKToolsLog` logger. Its log file goes to `AKTOOLS_LOG_DIR` if set (else the cwd, or `/tmp` on Vercel — `_log_path`), and falls back to the system temp dir when that location is not writable (`_create_log_handler`), because stdio MCP clients may launch it from an unwritable cwd. `tests/conftest.py` sets `AKTOOLS_LOG_DIR` to a temp dir before anything imports aktools, so tests never write `aktools_log.log` (or its midnight-rotated `aktools_log.log.YYYY-MM-DD`) into the repo.
- `aktools/core/catalog.py` — backs `/api/interfaces` (list + `?q=` search) and `/api/interfaces/{name}` by reading AKShare signatures and docstrings only (title = first line, source URL = second line, `:param`/`:type` lines); never calls an interface, so it works offline. `is_interface()` is also what `/api/public` uses to reject submodules/classes exported by `akshare`.
- The reserved query param `_format` (`json` default, `csv` with UTF-8 BOM, `xlsx` via openpyxl, which AKShare already depends on); it is popped before the AKShare call. AKShare parameters never start with `_`, which is why the reserved name is safe.
- `aktools/core/cache.py` — two caches used by `call_interface`: a TTL+LRU result cache keyed by `(interface, sorted params)` with `_format` excluded (`AKTOOLS_CACHE_TTL`, default 60s, response header `X-AKTools-Cache: hit|miss`), and `AkshareCacheJanitor`, which periodically calls `cache_clear()` on every `lru_cache` function found by walking all `akshare.*` modules (`AKTOOLS_AKSHARE_CACHE_CLEAR`, default 3600s). AKShare is built for short scripts, so its ~42 module-level `lru_cache`s (most are private, e.g. `__stock_board_concept_name_em`) never expire in a long-running server. Config travels as env vars so the CLI (`--cache-ttl`, `--akshare-cache-clear`), Gunicorn and Docker share one mechanism; `tests/conftest.py` gives every test a fresh result cache.
- `aktools/core/network.py` — reads `AKTOOLS_PROXY` / `AKTOOLS_TIMEOUT` (set by the CLI's `--proxy` / `--timeout`, or directly under Gunicorn, Docker, or an MCP client's `env`) once at import of `aktools.core.fetch` and applies them via `ak.set_proxies` / `ak.set_timeout` (AKShare ≥ 1.20.4; skipped with a log hint on older versions). The timeout is the read timeout; connect is fixed at 10s. Never apply these per request (e.g. `ak.ProxyContext`): AKShare's config is process-global and AKTools serves requests concurrently from a thread pool.
- `fetch_dataframe` maps AKShare's own exceptions (`akshare.exceptions`, which do not subclass `requests` errors) via `AKSHARE_ERRORS`: `NetworkError`→502, `RateLimitError`→429, `InvalidParameterError`→400, `APIError`/`DataParsingError`→502; anything else stays 404 "check usage / upgrade AKShare".
- `aktools/core/auth.py` — optional shared access tokens: `AKTOOLS_TOKEN` (CLI `--token`, comma-separated, never echoed) makes `TokenAuthMiddleware` require `Authorization: Bearer <t>` or `?_token=<t>` on `/api/*` and `/mcp`; `/`, `/version`, `/docs` and CORS preflight stay open. It is a pure ASGI middleware (never `BaseHTTPMiddleware`, which buffers the `/mcp` stream) and is added before CORS so 401s still carry CORS headers. `call_interface` pops `_token` so it never reaches AKShare or the cache key. Deliberately no user accounts/login (a demo login was removed in 0.0.93); per-person auth belongs in a gateway such as OAuth2 Proxy.
- `aktools/mcp_server.py` — MCP server, a required dependency pinned `mcp>=2.3,<3` (the v2 SDK, `MCPServer`, not v1's `FastMCP`; majors are API-incompatible). Two transports share one `MCPServer`: HTTP at `/mcp` inside the main app, and stdio via the `aktools-mcp` console script (`main()`), which AI clients launch themselves (`uvx --from aktools aktools-mcp`). In stdio mode `main()` swaps `sys.stdout` for an unbuffered stream on fd 1: the SDK diverts fd 1 to stderr during the session, but buffered `print` output from AKShare would otherwise flush onto the wire after the fd is restored (`test_stdio_stdout_carries_only_protocol_messages` checks the raw bytes). stdio mode has no HTTP server, so `get_data` returns `csv_url: null`. `MCPServer(...)` calls `logging.basicConfig(level=INFO)` on construction; `_create_server()` restores the root logger afterwards so importing AKTools never changes console output or an embedding app's logging. Exposes exactly three generic tools (`search_interfaces`, `describe_interface`, `get_data`) instead of one tool per interface, and `get_data` goes through `fetch_dataframe`, the same code path (cache, error mapping) as `/api/public`. Errors must be raised as `ToolError`; the SDK hides the text of any other exception. `aktools/main.py` registers it with `app.add_route("/mcp", ...)`, not `app.mount` (a mount 307-redirects `/mcp` to `/mcp/`, which MCP clients may not follow on POST). The host app's lifespan must run the session manager returned by `build_mcp_app`, because Starlette never runs a sub-app's lifespan. DNS-rebinding protection follows `AKTOOLS_HOST` (set by the CLI from `--host`, `0.0.0.0` in the Dockerfile): localhost-only unless the server listens on another address. Use `follow_redirects=False` when testing it with `TestClient`.
- `aktools/cli.py` — the `python -m aktools` / `aktools` entry point (Typer). The callback (with all the server options) starts the HTTP server unless a subcommand is given; `aktools mcp` runs the stdio MCP server and must print nothing to stdout. It launches `uvicorn aktools.main:app` as a subprocess; the command is passed as an argument list (not a shell string) so paths with spaces work.
- `aktools/datasets.py` — resolves bundled assets (the homepage template, favicon) via `importlib.resources`. These files ship inside the wheel; `[tool.setuptools.package-data]` in `pyproject.toml` controls what is included.
- `aktools/utils.py` — `get_latest_version()` queries PyPI for the newest AKShare/AKTools version shown on the homepage and `/version`, caching successes for 1h and failures for 5min. It blocks on the network, so those two routes are plain `def` (run in the thread pool) — making them `async` would freeze every other request, including `/mcp`, whenever PyPI is slow or unreachable. Tests that render the homepage must stub this to stay offline.
- `src/app.py` — the Vercel entry point; it just re-exports `app`.
- `Dockerfile` — installs `akshare` and `aktools` from PyPI (not from this checkout; `.dockerignore` excludes everything), so an image only reflects released versions. `BASE_IMAGE` and `PIP_INDEX_URL` build args exist because Docker Hub and official PyPI are usually unreachable from China (e.g. `docker.m.daocloud.io/library/python:3.14-slim-trixie`). Gunicorn runs 1 worker unless `WEB_CONCURRENCY` is set.
- `.readthedocs.yaml` — installs only the `docs` group with `uv sync --locked --only-group docs` and runs `zensical build --strict`. Its pinned `uv==` version must match `UV_VERSION` in `build.yml`.

## Conventions

- **Packaging metadata lives in `pyproject.toml`** (there is no `setup.py`). The version is read dynamically from `__version__` in `aktools/_version.py` (re-exported by `aktools/__init__.py`).
- **A release bumps four places that must agree**, enforced by `scripts/check_release.py` in the release workflow: the git tag (`vX.Y.Z`), `__version__` in `aktools/_version.py`, a `X.Y.Z: ...` entry in `docs/aktools_version.md`, and both `version` fields in `server.json` (server and PyPI package). The version history lives only in `docs/aktools_version.md` — do not re-add a copy to the package.
- Releasing: push a `vX.Y.Z` tag; `release_and_deploy.yml` verifies metadata, builds, checks the artifacts, uploads to PyPI, then creates the GitHub release. A separate `publish-mcp-registry` job then publishes `server.json` to the official MCP Registry as `io.github.akfamily/aktools` via GitHub OIDC (no secret), using a cosign-verified `mcp-publisher` pinned by `MCP_PUBLISHER_VERSION`. The registry proves PyPI ownership by finding `<!-- mcp-name: io.github.akfamily/aktools -->` in that version's PyPI description, so the marker must stay in `README.md` (`test_readme_carries_mcp_registry_ownership_marker` guards it). Registry clients start PyPI servers as `uvx <package>`, which is why `server.json` declares `uvx aktools mcp` and the `aktools` console script exists. If only that job fails, re-run it; no new release is needed.
- Python 3.11+ only, matching current AKShare. Commit messages follow Conventional Commits (checked by the `commit-msg` hook). PRs target `main`.
