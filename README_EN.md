[简体中文](https://github.com/akfamily/aktools/blob/main/README.md) | **English**

# AKTools

> AKTools exposes [AKShare](https://github.com/akfamily/akshare)'s financial data as an HTTP API and an MCP server, so you can fetch it from any programming language or AI assistant.

[![PyPI](https://img.shields.io/pypi/v/aktools.svg)](https://pypi.org/project/aktools/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aktools.svg)](https://pypi.org/project/aktools/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/aktools?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/aktools)
[![Documentation Status](https://img.shields.io/readthedocs/aktools/latest)](https://aktools.akfamily.xyz/)
[![Actions Status](https://github.com/akfamily/aktools/actions/workflows/build.yml/badge.svg)](https://github.com/akfamily/aktools/actions/workflows/build.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Data Science - AKShare](https://img.shields.io/badge/Data%20Science-AKShare-green)](https://github.com/akfamily/akshare)
[![MIT Licence](https://img.shields.io/badge/license-MIT-blue)](https://github.com/akfamily/aktools/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/akfamily/aktools)](https://github.com/akfamily/aktools/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/akfamily/aktools)](https://github.com/akfamily/aktools/network/members)
[![GitHub issues](https://img.shields.io/github/issues/akfamily/aktools)](https://github.com/akfamily/aktools/issues)

[AKTools](https://github.com/akfamily/aktools) turns the nearly one thousand interfaces of [AKShare](https://github.com/akfamily/akshare), an open-source financial data library, into two ready-to-use services:

- **HTTP API**: start a server with one command, then fetch data by URL from C/C++, Java, Go, Rust, JavaScript, R, MATLAB, Stata, Excel or anything else that can send an HTTP request.
- **MCP server**: ask in natural language inside WorkBuddy, Codex, Cursor, Claude and other AI assistants; the assistant finds the interface, fills in the parameters and fetches the data itself.

Both share the same interface catalog, cache and error handling, so use whichever fits.

**[Documentation (Chinese)](https://aktools.akfamily.xyz/)** | **[AKShare data dictionary (Chinese)](https://akshare.akfamily.xyz/data/index.html)** | **[Release notes (Chinese)](https://aktools.akfamily.xyz/aktools_version/)**

> **Notes for English readers**: the documentation site, interface titles, most column names and error messages are in Chinese, because AKShare's data sources are mainly Chinese financial websites. Interface names and parameter names are in English. Many data sources are only reachable from mainland China.

## Contents

- [Two ways to use it](#two-ways-to-use-it)
- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [How a request maps to AKShare](#how-a-request-maps-to-akshare)
- [Examples in several languages](#examples-in-several-languages)
- [Deployment](#deployment)
- [FAQ](#faq)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

## Two ways to use it

### Fetch data over the HTTP API

```shell
pip install aktools
python -m aktools
```

Then open `http://127.0.0.1:8080/api/public/calendar_trade_date_hist_sina` in a browser. Seeing the trading calendar means it works. See [Quick start](#quick-start) and [How a request maps to AKShare](#how-a-request-maps-to-akshare) below for more.

### Use it in an AI assistant

[Install uv](https://docs.astral.sh/uv/getting-started/installation/), then add the configuration below to your assistant's MCP configuration file. **You do not need to install AKTools first or start a server yourself**:

```json
{
  "mcpServers": {
    "aktools": {
      "command": "uvx",
      "args": ["--from", "aktools", "aktools-mcp"]
    }
  }
}
```

Restart the assistant and ask, for example:

- "Get the forward-adjusted daily bars of Kweichow Moutai (600519) from 8 to 11 October 2024"
- "Which AKShare interfaces are about convertible bonds?"
- "What parameters does stock_zh_a_hist_em take, and how do I set the price adjustment?"

The assistant answers with three tools provided by AKTools: `search_interfaces` finds interfaces, `describe_interface` shows their parameters and `get_data` fetches the data. Below is a real question asked in Claude Code (replayed from an actual session, in Chinese):

![A question asked in Claude Code; the assistant queries the daily bars of Kweichow Moutai through the AKTools MCP tools](https://aktools.akfamily.xyz/img/mcp-demo.gif)

> **Backtesting with AKQuant in one sentence**: ask WorkBuddy to "install the official MCP servers of AKShare and AKQuant, run a sample strategy and report the results". The assistant downloads the data, runs the backtest, explains the results and suggests improvements. See [Using it with AKQuant](https://aktools.akfamily.xyz/guide/mcp/#akquant) (Chinese).

<details>
<summary>WorkBuddy</summary>

Tell WorkBuddy to "install the official MCP server of AKShare" and it configures itself. You can also add the configuration above to WorkBuddy's connector (MCP) settings, or to the user-level file `~/.workbuddy/mcp.json`. In mainland China, add `"env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}` under `aktools` to use a PyPI mirror.

</details>

<details>
<summary>Codex</summary>

```shell
codex mcp add aktools -- uvx --from aktools aktools-mcp
```

</details>

<details>
<summary>Cursor</summary>

Add it with one click:

[![Add AKTools MCP server to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=aktools&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJha3Rvb2xzIiwiYWt0b29scy1tY3AiXX0%3D)

Or add the configuration above to `.cursor/mcp.json` in your project, or to the global `~/.cursor/mcp.json`.

</details>

<details>
<summary>Claude Code</summary>

```shell
claude mcp add aktools -- uvx --from aktools aktools-mcp
```

</details>

<details>
<summary>Claude Desktop</summary>

Open "Developer → Edit Config" in the settings, add the configuration above to `claude_desktop_config.json`, save and restart Claude Desktop.

</details>

<details>
<summary>Connect to an AKTools server that is already running (HTTP)</summary>

If you have already started a server with `python -m aktools`, or want several computers to share one server, point the assistant at `http://127.0.0.1:8080/mcp`, for example:

```shell
claude mcp add --transport http aktools http://127.0.0.1:8080/mcp
```

</details>

On first start `uvx` downloads AKShare and its dependencies (about 150 MB), which can take a few minutes. For configuration, LAN access and troubleshooting, see the [AI assistant (MCP) guide](https://aktools.akfamily.xyz/guide/mcp/) (Chinese).

## Features

- **Two ways in**: the same data is available over the HTTP API and, in natural language, in WorkBuddy, Codex, Cursor, Claude and other AI assistants
- **Zero configuration**: `python -m aktools` starts the server, with no code to write
- **Every interface covered**: each AKShare data interface is available at `/api/public/<interface name>`; when AKShare adds one, upgrading is enough
- **Any language**: responses are standard JSON, usable from anything that can send an HTTP request
- **Self-describing**: `/api/interfaces` lists every interface and supports keyword search; each interface's parameters, defaults and descriptions can be queried directly
- **Table downloads**: add `_format=csv` or `_format=xlsx` to download the data as a CSV or Excel file
- **Result cache**: the same interface with the same parameters returns the previous result for 60 seconds, which reduces repeated requests to upstream websites and the risk of an IP ban
- **Built-in docs**: built on [FastAPI](https://fastapi.tiangolo.com/); open `/docs` after starting to browse and try the API
- **Easy to deploy**: ships a Dockerfile and supports multi-process deployment with Gunicorn + Uvicorn

## Installation

AKTools requires **64-bit Python 3.11.5 or later**. The environment requirements are the same as in the [AKShare installation guide](https://akshare.akfamily.xyz/installation.html) (Chinese).

```shell
pip install aktools
```

AKShare's interfaces change often, following the upstream websites. If something goes wrong, upgrade both packages first:

```shell
pip install akshare aktools --upgrade -i https://pypi.org/simple
```

## Quick start

1. Start the server:

    ```shell
    python -m aktools
    ```

2. Open these addresses in a browser:

    | Address | What it shows |
    | --- | --- |
    | `http://127.0.0.1:8080/` | Home page with brief instructions |
    | `http://127.0.0.1:8080/docs` | API browser, with online debugging |
    | `http://127.0.0.1:8080/version` | Installed and latest versions of AKShare and AKTools |
    | `http://127.0.0.1:8080/api/interfaces?q=历史行情` | Search interfaces by keyword; titles are in Chinese (here "historical quotes"), English name fragments such as `stock_zh_a` also work |
    | `http://127.0.0.1:8080/api/interfaces/stock_zh_a_hist_em` | Parameters, defaults and descriptions of one interface |
    | `http://127.0.0.1:8080/api/public/calendar_trade_date_hist_sina` | Connectivity test (Sina trading calendar; needs no parameters and is fairly stable) |
    | `http://127.0.0.1:8080/api/public/stock_zh_a_hist_em?symbol=600000` | Fetch data with a parameter |

Command-line options:

| Option | Short | Default | Description |
| --- | --- | --- | --- |
| `--host` | `-H` | `127.0.0.1` | Address to listen on; set to `0.0.0.0` to allow access from the LAN or other machines |
| `--port` | `-P` | `8080` | Port to listen on |
| `--auto` | `-A` | off | Open the browser after starting |
| `--cache-ttl` | — | `60` | Lifetime of the result cache in seconds; the same interface with the same parameters returns the previous result within it; `0` disables it |
| `--akshare-cache-clear` | — | `3600` | Interval in seconds for clearing AKShare's internal caches, so data such as board names does not stay stale; `0` disables it |
| `--proxy` | — | unset | Proxy for requests to upstream data sources, e.g. `http://127.0.0.1:7890`; when unset, environment variables such as `HTTP_PROXY` apply |
| `--timeout` | — | `60` | Read timeout in seconds for requests to upstream data sources; the connect timeout is fixed at 10 seconds |
| `--token` | — | unset | Access token; when set, the data endpoints and `/mcp` require it; separate several tokens with commas; see [Access tokens](https://aktools.akfamily.xyz/deploy/#token) (Chinese) |
| `--version` | `-v` | — | Show the AKTools version |

For example, `python -m aktools --port 8888 --auto` starts on port 8888 and opens the browser. To allow other machines on the LAN, add `--host 0.0.0.0`; they then use `http://<this machine's IP>:8888`. `0.0.0.0` only means "listen on all network interfaces" and cannot be opened in a browser as an address.

## How a request maps to AKShare

AKTools does not process the data. It only translates an HTTP request into a call to the AKShare interface:

```text
GET /api/public/{interface}?{param1}={value1}&{param2}={value2}
        ↓
akshare.{interface}(param1="value1", param2="value2")
```

- **The interface name** is exactly the AKShare function name. Search with `/api/interfaces?q=keyword`, read the parameters at `/api/interfaces/{interface}`, and see the [AKShare data dictionary](https://akshare.akfamily.xyz/data/index.html) (Chinese) for what the data means.
- **Parameters** go in the query string, with no quotes around values, e.g. `?symbol=600000&period=weekly`. Parameters you leave out take the AKShare defaults.
- **The response** is by default a JSON array, one object per DataFrame row. Date-time fields are in ISO 8601 format, e.g. `"2024-01-25T00:00:00.000"`.
- **Table downloads**: add the reserved parameter `_format=csv` or `_format=xlsx` and the data is downloaded as `{interface}.csv` or `{interface}.xlsx`, e.g. `/api/public/stock_zh_a_hist_em?symbol=000001&_format=xlsx`. The CSV is UTF-8 with a BOM, so Excel opens it directly.

A failed request returns `{"error": "message"}` (the message is in Chinese) with one of these status codes:

| Status | Meaning | What to do |
| --- | --- | --- |
| `200` | Success | — |
| `401` | The server requires an access token and the request carries none or a wrong one | Add the header `Authorization: Bearer <token>`, or `_token=<token>` to the URL |
| `400` | Invalid parameter name or value, unsupported `_format`, or more rows than Excel allows | Check the parameters against `/api/interfaces/{interface}`; use `json`, `csv` or `xlsx` for `_format`, and `csv` for very large tables |
| `404` | Unknown interface name, or the call failed | Upgrade AKShare and check the name and parameters against `/api/interfaces/{interface}` |
| `429` | The upstream data source is rate-limiting | Retry later, or raise `--cache-ttl` to reduce repeated requests |
| `502` | The upstream data source is unreachable or returned an error, or its page changed and parsing failed | Check the network and proxy settings, see [FAQ](#faq); upgrade AKShare if parsing failed |

## Examples in several languages

The examples assume the server runs at `http://127.0.0.1:8080`; change the address and port to match yours.

<details open>
<summary>curl</summary>

```shell
curl "http://127.0.0.1:8080/api/public/stock_zh_a_hist_em?symbol=000001&period=daily&start_date=20240101&end_date=20240131&adjust=qfq"
```

</details>

<details>
<summary>Python</summary>

```python
import pandas as pd
import requests

url = "http://127.0.0.1:8080/api/public/stock_zh_a_hist_em"
params = {
    "symbol": "000001",
    "period": "daily",
    "start_date": "20240101",
    "end_date": "20240131",
    "adjust": "qfq",
}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
df = pd.DataFrame(r.json())
print(df)
```

</details>

<details>
<summary>R</summary>

```r
library(RCurl)    # install the package first
library(jsonlite) # install the package first
options(warn = -1) # silence the warning for requests without parameters

temp_df <- getForm(
  uri = "http://127.0.0.1:8080/api/public/stock_zh_a_hist_em",
  symbol = "000001",
  period = "daily",
  start_date = "20211109",
  end_date = "20211209",
  adjust = "hfq",
  .encoding = "utf-8"
)
inner_df <- fromJSON(temp_df)
inner_df
```

</details>

<details>
<summary>MATLAB</summary>

```matlab
api = 'http://127.0.0.1:8080/api/public/';
url = [api 'stock_zh_a_hist_em'];
options = weboptions('ContentType', 'json', 'CharacterEncoding', 'utf-8');
data = webread(url, 'symbol', '000001', 'period', 'daily', ...
    'start_date', '20211109', 'end_date', '20211209', 'adjust', 'hfq', options);
data % MATLAB cannot display Chinese field names; rename them to English if needed
```

</details>

<details>
<summary>Rust</summary>

Dependencies: `reqwest` (with the `blocking` and `json` features) and `serde_json`.

```rust
use reqwest::blocking;
use serde_json::Value;

const URL: &str = "http://127.0.0.1:8080/api/public";

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let params = [
        ("symbol", "000001"),
        ("period", "daily"),
        ("start_date", "20240125"),
        ("end_date", "20240126"),
        ("adjust", ""),
    ];
    let resp = blocking::Client::new()
        .get(format!("{URL}/stock_zh_a_hist_em"))
        .query(&params)
        .send()?;

    if resp.status().is_success() {
        let data: Value = resp.json()?;
        println!("{data:#?}");
    } else {
        eprintln!("Request failed with status {}", resp.status());
    }
    Ok(())
}
```

</details>

For more examples and their output, see [Examples in other languages](https://aktools.akfamily.xyz/guide/examples/) (Chinese).

## Deployment

### Docker

Build an image from the [Dockerfile](https://github.com/akfamily/aktools/blob/main/Dockerfile) in this repository. The image runs Gunicorn with Uvicorn workers; set the number of workers with `-e WEB_CONCURRENCY=4`:

```shell
docker build -t aktools .
docker run -d -p 8080:8080 aktools
```

Docker Hub and the official PyPI are usually unreachable from mainland China; mirrors can be given for each:

```shell
docker build --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.14-slim-trixie --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t aktools .
```

For upgrading the image and more, see the [deployment guide](https://aktools.akfamily.xyz/deploy/#docker) (Chinese).

### Production

`python -m aktools` is meant for local use. In production, start `aktools.main:app` with Gunicorn directly:

```shell
pip install gunicorn uvicorn-worker
AKTOOLS_HOST=0.0.0.0 gunicorn aktools.main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn_worker.UvicornWorker
```

> When several people or computers share a server, set an access token with `--token`; see [Access tokens](https://aktools.akfamily.xyz/deploy/#token) (Chinese). AKTools has no user accounts; to manage permissions per person, put an authenticating reverse proxy in front of it.

## FAQ

**502, "访问上游数据源失败" (failed to reach the upstream data source)**

The machine running AKTools cannot reach upstream websites such as Eastmoney or Sina Finance, usually because of the proxy configuration. If the error mentions `ProxyError` or `Unable to connect to proxy`, check or clear the proxy environment variables and restart the server:

```shell
# Linux / macOS
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
# Windows PowerShell
Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:ALL_PROXY
```

Some interfaces can only be reached from a network in mainland China; see the notes for the interface in the AKShare documentation.

**404, "未找到该接口" (interface not found) or "调用接口出错" (the call failed)**

Upgrade AKShare first, then search for the right name with `/api/interfaces?q=keyword` and check the parameter names and allowed values at `/api/interfaces/{interface}`. You can also call the AKShare function of the same name in Python to see whether the problem is in AKShare.

**The data is not up to date**

Requests for the same interface with the same parameters return cached data for 60 seconds; the response header `X-AKTools-Cache: hit` means the data came from the cache. Start with `--cache-ttl 0` to turn the cache off. Data such as board names is cached inside AKShare and cleared every hour by default, adjustable with `--akshare-cache-clear`.

**Where do I report wrong data or a failing interface?**

AKTools only forwards requests; the data comes from AKShare. If calling AKShare directly in Python shows the same problem, report it at [AKShare Issues](https://github.com/akfamily/akshare/issues). Report only problems of AKTools itself (startup, routing, serialization and so on) at [AKTools Issues](https://github.com/akfamily/aktools/issues).

## Contributing

Issues and pull requests are welcome. For the development setup, code checks and commit conventions, see the [contributing guide](https://github.com/akfamily/aktools/blob/main/CONTRIBUTING.md) (Chinese). By participating you agree to follow the [code of conduct](https://github.com/akfamily/aktools/blob/main/CODE_OF_CONDUCT.md).

## Disclaimer

The data provided by AKTools and AKShare is for academic research only and is not investment advice. All of it comes from public data sources on the internet; verify it before use and follow the terms of use of each data source. The authors and contributors accept no liability for any direct or indirect loss caused by using this project.

## License

This project is open source under the [MIT License](https://github.com/akfamily/aktools/blob/main/LICENSE).
