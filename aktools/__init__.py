"""AKTools 是 AKShare 的 HTTP API 工具, 主要目的是使 AKShare 的数据接口部署到本地从而通过 HTTP 访问来获取所需要的数据"""

"""
Changelog

0.0.1: for test
0.0.2: FastAPI test
0.0.3: FastAPI deployment test
0.0.4: add docs
0.0.5: add automate package management
0.0.6: add automate package management success
0.0.7: add automate release test
0.0.8: add automate release test again
0.0.9: add automate success
0.0.10: fix: rename workflows
0.0.11: fix: README.md
0.0.12: fix: README.md
0.0.13: fix: test pull_request
0.0.14: fix: test master push tag
0.0.15: fix: update PYPI info
0.0.16: fix: update PYPI info
0.0.17: fix: update PYPI info
0.0.18: add: add params to interface
0.0.19: fix: rename file name
0.0.20: fix: rename api name
0.0.21: fix: rename api name
0.0.22: fix: fix core module
0.0.23: fix: fix core module
0.0.24: fix: fix chinese character params in api
0.0.25: test: test
0.0.26: test: test
0.0.27: test: test
0.0.28: test: test
0.0.29: test: test
0.0.30: add: add cmd arg parser
0.0.31: add: add cmd arg parser -d
0.0.32: fix: fix docs
0.0.33: fix: fix return result
0.0.34: fix: fix return None
0.0.35: add: add multiple threads support for multiple requests
0.0.36: fix: update PYPI info
0.0.37: fix: update workflow info
0.0.38: fix: fix docs
0.0.39: fix: fix docs
0.0.40: fix: fix docs
0.0.41: fix: fix docs
0.0.42: fix: fix email
0.0.43: add: add support response status code
0.0.44: add: add login support
0.0.45: add: add module format support
0.0.46: fix: fix setup.py
0.0.47: add: add tips
0.0.48: fix: fix docs
0.0.49: add: add FastAPI docs introduction
0.0.50: add: add interface docs
0.0.51: add: add CORS support
0.0.52: add: add PyScript demo
0.0.53: fix: fix PyScript demo url
0.0.54: fix: fix PyScript demo url
0.0.55: add: add datasets.py
0.0.56: add: add init.py
0.0.57: fix: fix setup.py
0.0.58: add: add jinja2 to setup.py
0.0.59: add: add templates
0.0.60: add: add css and html to akscript.html
0.0.61: fix: fix remove dependency from akscript.html
0.0.62: add: add favicon.ico
0.0.63: fix: fix favicon.ico path
0.0.64: fix: fix favicon.ico path
0.0.65: fix: fix favicon.ico path
0.0.66: fix: fix setup.py
0.0.67: fix: fix parameter with blank character
0.0.68: fix: fix cookie in parameter
0.0.69: fix: fix file path in datasets.py
0.0.70: add: add homepage
0.0.71: add: add more info to homepage
0.0.72: add: add type hint for CLI
0.0.73: fix: fix tips
0.0.74: add: add typer for CLI
0.0.75: add: add version interface
0.0.76: fix: fix rename master to main
0.0.77: add: add cli.py file
0.0.78: add: add test_cli.py
0.0.79: fix: fix typos in homepage.html
0.0.80: fix: fix uvicorn run command
0.0.81: add: add support for Python 3.11
"""

__title__ = "AKTools"
__version__ = "0.0.81"
__author__ = "AKFamily"
