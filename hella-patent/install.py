#!/usr/bin/env python3
"""把 hella-patent 安装到 Cursor 能加载的技能目录。"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
SKILL_NAME = "hella-patent"
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".git"}


def ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in SKIP_DIRS or name.endswith(".pyc")}


def same_tree(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return False


def skills_dir(project: Path | None, user: bool) -> Path:
    if user:
        return Path.home() / ".cursor" / "skills"
    return (project or Path.cwd()).resolve() / ".cursor" / "skills"


def install(destination_root: Path, force: bool) -> Path:
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / SKILL_NAME
    if same_tree(destination, PACKAGE):
        print(f"SKILL_INSTALL: ok=1 mode=inplace dest={destination}")
        return destination
    try:
        inside = destination.resolve().is_relative_to(PACKAGE.resolve())
    except OSError:
        inside = False
    if inside:
        print("SKILL_INSTALL: ok=0 不能把技能安装到它自己的目录里", file=sys.stderr)
        raise SystemExit(2)
    if destination.exists() or destination.is_symlink():
        if not force:
            print(
                f"SKILL_INSTALL: ok=0 exists={destination} 加上 --force 后覆盖",
                file=sys.stderr,
            )
            raise SystemExit(1)
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    shutil.copytree(PACKAGE, destination, ignore=ignore)
    print(f"SKILL_INSTALL: ok=1 mode=copy dest={destination}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="安装 hella-patent Cursor 技能")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, help="安装到该项目的 .cursor/skills")
    target.add_argument("--user", action="store_true", help="安装到当前用户的 ~/.cursor/skills")
    parser.add_argument("--force", action="store_true", help="目标已存在时覆盖")
    args = parser.parse_args()
    if not (PACKAGE / "SKILL.md").is_file():
        print("SKILL_INSTALL: ok=0 缺少 SKILL.md", file=sys.stderr)
        return 2
    install(skills_dir(args.project, args.user), args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
