# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: 发布前版本元数据校验脚本的测试
"""

import pathlib

import pytest

from check_release import collect_problems, has_version_entry, parse_tag, read_version


def make_repo(tmp_path, version="0.0.92", changelog_version=None):
    """
    构造只含发布校验所需两个文件的最小仓库
    :param tmp_path: pytest 提供的临时目录
    :param version: 写入 __init__.py 的版本号
    :param changelog_version: 写入版本说明的版本号，默认与 version 相同
    :return: 仓库根目录
    """
    changelog_version = version if changelog_version is None else changelog_version
    (tmp_path / "aktools").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "aktools" / "__init__.py").write_text(
        f'__title__ = "AKTools"\n__version__ = "{version}"\n', encoding="utf-8"
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
    assert len(problems) == 1
    assert "不一致" in problems[0]


def test_collect_problems_detects_missing_changelog_entry(tmp_path):
    repo = make_repo(tmp_path, changelog_version="0.0.91")
    problems = collect_problems(repo, "v0.0.92")
    assert len(problems) == 1
    assert "aktools_version.md" in problems[0]


def test_collect_problems_reports_every_problem_at_once(tmp_path):
    """一次报全，避免修一个再跑一次 CI 才发现下一个"""
    repo = make_repo(tmp_path, changelog_version="0.0.91")
    assert len(collect_problems(repo, "v0.0.99")) == 2


def test_current_repo_is_consistent():
    """仓库自身的版本号必须已写入版本说明，发布前即可在 CI 中发现遗漏"""
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    version = read_version(repo_root / "aktools" / "__init__.py")
    assert collect_problems(repo_root, f"v{version}") == []
