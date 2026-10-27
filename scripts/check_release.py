# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: 发布前校验版本元数据自洽，供 release_and_deploy.yml 在构建与上传之前调用

必须在 twine upload 之前运行：PyPI 的版本号一经占用即不可重用，
发错版本号只能改用下一个号，无法撤回。

校验三处必须一致：
    1. git tag（v0.0.92）
    2. aktools/_version.py 中的 __version__
    3. docs/aktools_version.md 的版本条目（行首为「0.0.92: 」）

本脚本只依赖标准库，因此 CI 中无需安装任何依赖即可运行。
"""

import argparse
import pathlib
import re
from typing import List

TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+)$")
VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.M)


def parse_tag(tag: str) -> str:
    """
    从 git tag 中取出版本号
    :param tag: 形如 v0.0.92 的 tag 名
    :type tag: str
    :return: 版本号
    :rtype: str
    """
    match = TAG_RE.match(tag)
    if not match:
        raise ValueError(f"tag 格式不合法，应为 vX.Y.Z，实际为 {tag!r}")
    return match.group(1)


def read_version(path: pathlib.Path) -> str:
    """
    读取 aktools/_version.py 中声明的版本号
    按文件读取加正则提取，不 import 本包，因此无需安装 aktools 及其依赖
    :param path: _version.py 的路径
    :type path: pathlib.Path
    :return: 版本号
    :rtype: str
    """
    match = VERSION_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path} 中未找到 __version__ 声明")
    return match.group(1)


def has_version_entry(text: str, version: str) -> bool:
    """
    判断版本说明中是否存在该版本的条目
    条目使用「0.0.92: type: desc」的行首格式；锚定行首与冒号，
    避免 0.0.9 被 0.0.92 的条目或正文中的引用误判为存在
    :param text: 版本说明全文
    :type text: str
    :param version: 版本号
    :type version: str
    :return: 是否存在对应条目
    :rtype: bool
    """
    return re.search(rf"^{re.escape(version)}: ", text, re.M) is not None


def collect_problems(repo_root: pathlib.Path, tag: str) -> List[str]:
    """
    汇总全部不一致项，一次性报出而非遇到第一个就退出
    :param repo_root: 仓库根目录
    :type repo_root: pathlib.Path
    :param tag: git tag 名
    :type tag: str
    :return: 问题描述列表，为空表示校验通过
    :rtype: List[str]
    """
    problems: List[str] = []
    tag_version = parse_tag(tag)
    file_version = read_version(repo_root / "aktools" / "_version.py")

    if tag_version != file_version:
        problems.append(
            f"tag 版本 {tag_version} 与 aktools/_version.py 的 {file_version} 不一致"
        )

    changelog_text = (repo_root / "docs" / "aktools_version.md").read_text(
        encoding="utf-8"
    )
    if not has_version_entry(changelog_text, file_version):
        problems.append(f"docs/aktools_version.md 缺少 {file_version} 的版本说明")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="校验发布版本元数据是否自洽")
    parser.add_argument("tag", help="git tag 名，形如 v0.0.92")
    args = parser.parse_args()
    repo_root = pathlib.Path(__file__).resolve().parent.parent

    try:
        problems = collect_problems(repo_root, args.tag)
    except ValueError as err:
        print(f"[release] {err}")
        return 1

    if problems:
        for problem in problems:
            print(f"[release] {problem}")
        print("[release] 校验失败，已阻止发布")
        return 1

    print(f"[release] 版本元数据校验通过：{parse_tag(args.tag)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
