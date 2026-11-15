# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: 发布前版本元数据校验脚本的测试
"""

import json
import pathlib

import pytest

from check_release import collect_problems, has_version_entry, parse_tag, read_version


def make_repo(tmp_path, version="0.0.92", changelog_version=None, server_versions=None):
    """
    构造只含发布校验所需文件的最小仓库
    :param tmp_path: pytest 提供的临时目录
    :param version: 写入 _version.py 的版本号
    :param changelog_version: 写入版本说明的版本号，默认与 version 相同
    :param server_versions: 写入 server.json 的 (服务版本, PyPI 包版本)，默认均与 version 相同
    :return: 仓库根目录
    """
    changelog_version = version if changelog_version is None else changelog_version
    server_version, package_version = server_versions or (version, version)
    (tmp_path / "server.json").write_text(
        json.dumps(
            {
                "name": "io.github.akfamily/aktools",
                "version": server_version,
                "packages": [
                    {
                        "registryType": "pypi",
                        "identifier": "aktools",
                        "version": package_version,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "aktools").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "aktools" / "_version.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )
    (tmp_path / "docs" / "aktools_version.md").write_text(
        f"## 开发进度\n\n{changelog_version}: fix: fix something\n", encoding="utf-8"
    )
    return tmp_path


def test_parse_tag_extracts_version():
    assert parse_tag("v0.0.92") == "0.0.92"


@pytest.mark.parametrize(
    "tag", ["release-v0.0.92", "v0.0", "0.0.92", "v0.0.92-rc1", "V0.0.92", ""]
)
def test_parse_tag_rejects_malformed(tag):
    """tag 格式必须严格，否则版本号可能被截取成意料之外的值"""
    with pytest.raises(ValueError):
        parse_tag(tag)


def test_read_version(tmp_path):
    path = tmp_path / "__init__.py"
    path.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    assert read_version(path) == "1.2.3"


def test_read_version_without_declaration_raises(tmp_path):
    path = tmp_path / "__init__.py"
    path.write_text("# 没有版本声明\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_version(path)


def test_has_version_entry_requires_line_start():
    """必须锚定行首与冒号，否则 0.0.9 会被 0.0.92 的条目误判为存在"""
    text = "0.0.92: fix: something\n"
    assert has_version_entry(text, "0.0.92")
    assert not has_version_entry(text, "0.0.9")
    assert not has_version_entry("见 0.0.92: 的说明\n", "0.0.92")


def test_collect_problems_passes_when_all_aligned(tmp_path):
    assert collect_problems(make_repo(tmp_path), "v0.0.92") == []


def test_collect_problems_detects_tag_version_mismatch(tmp_path):
    problems = collect_problems(make_repo(tmp_path), "v0.0.99")
    # _version.py 与 server.json 都和 tag 不一致，各报一条
    assert len(problems) == 2
    assert "_version.py" in problems[0] and "server.json" in problems[1]


def test_collect_problems_detects_missing_changelog_entry(tmp_path):
    repo = make_repo(tmp_path, changelog_version="0.0.91")
    problems = collect_problems(repo, "v0.0.92")
    assert len(problems) == 1
    assert "aktools_version.md" in problems[0]


def test_collect_problems_reports_every_problem_at_once(tmp_path):
    """一次报全，避免修一个再跑一次 CI 才发现下一个"""
    repo = make_repo(tmp_path, changelog_version="0.0.91")
    # _version.py、版本说明、server.json 三处问题一次报出
    assert len(collect_problems(repo, "v0.0.99")) == 3


def test_current_repo_is_consistent():
    """仓库自身的版本号必须已写入版本说明，发布前即可在 CI 中发现遗漏"""
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    version = read_version(repo_root / "aktools" / "_version.py")
    assert collect_problems(repo_root, f"v{version}") == []


@pytest.mark.parametrize(
    "server_versions", [("0.0.91", "0.0.92"), ("0.0.92", "0.0.91")]
)
def test_collect_problems_detects_server_json_mismatch(tmp_path, server_versions):
    """MCP 注册表按 server.json 登记版本，服务版本与 PyPI 包版本都必须与 tag 一致"""
    repo = make_repo(tmp_path, server_versions=server_versions)
    problems = collect_problems(repo, "v0.0.92")
    assert len(problems) == 1
    assert "server.json" in problems[0]


def test_readme_carries_mcp_registry_ownership_marker():
    """
    MCP 官方注册表通过 PyPI 上的项目说明（即 README）中的 mcp-name 标记确认包的归属，
    标记中的名称必须与 server.json 的 name 完全一致，否则登记会失败
    """
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    name = json.loads((repo_root / "server.json").read_text(encoding="utf-8"))["name"]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert f"<!-- mcp-name: {name} -->" in readme.splitlines()


def test_readmes_stay_in_step():
    """
    README.md（中文，默认显示，也是 PyPI 项目说明）与 README_EN.md（英文）互相链接，
    章节数量、示例中的接口名与 MCP 配置片段保持一致，且接口名都真实存在：
    AKShare 改名后只改了其中一个文件，另一个里的示例就会失效
    """
    import re

    from aktools.core.catalog import is_interface

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    zh = (repo_root / "README.md").read_text(encoding="utf-8")
    en = (repo_root / "README_EN.md").read_text(encoding="utf-8")
    base = "https://github.com/akfamily/aktools/blob/main"
    assert zh.splitlines()[0] == f"**简体中文** | [English]({base}/README_EN.md)"
    assert en.splitlines()[0] == f"[简体中文]({base}/README.md) | **English**"

    def headings(text):
        return [
            line.split(" ")[0] for line in text.splitlines() if line.startswith("#")
        ]

    def interfaces(text):
        names = re.findall(r"/api/(?:public|interfaces)/([a-z][a-z0-9_]+)", text)
        return sorted(set(names))

    def code_blocks(text):
        # 代码块中的注释与提示文字随语言不同，只比较不含中文和注释的行
        blocks = re.findall(r"```(?:shell|json|text)\n(.*?)```", text, flags=re.S)
        lines = [line.strip() for block in blocks for line in block.splitlines()]
        return [line for line in lines if line and line.isascii() and "#" not in line]

    assert headings(zh) == headings(en)
    assert interfaces(zh) == interfaces(en)
    assert interfaces(zh) and all(is_interface(name) for name in interfaces(zh))
    assert zh.count("<summary>") == en.count("<summary>")
    assert [line for line in code_blocks(zh) if "{" not in line or "mcp" in line] == [
        line for line in code_blocks(en) if "{" not in line or "mcp" in line
    ]
    assert '"args": ["--from", "aktools", "aktools-mcp"]' in en
