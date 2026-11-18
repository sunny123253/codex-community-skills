#!/usr/bin/env python3
"""Restricted MCP writer for generated knowledge-base artifacts."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from typing import Iterable


TEXT_DIR_NAME = "文本"
ALLOWED_KINDS = {"摘要", "综述", "笔记", "证据包"}
PROTECTED_ROOTS = (Path(r"E:\projects\obsidian\01-library"), Path(r"E:\zotero file\storage"))


class WriterPolicyError(ValueError):
    """Raised when a requested write falls outside the writer policy."""


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_protected(path: Path) -> bool:
    if any(part.lower() == "01-library" for part in path.parts):
        return True
    return any(_is_relative_to(path, protected.resolve()) for protected in PROTECTED_ROOTS)


def _project_root(project_root: str | os.PathLike[str]) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise WriterPolicyError(f"项目目录不存在: {root}")
    if _is_protected(root):
        raise WriterPolicyError("不能在 01-library 或 Zotero 存储目录中创建输出")
    return root


def _safe_slug(title: str) -> str:
    slug = re.sub(r'[<>:"/\\|?*]+', "-", (title or "").strip())
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip(".- ")
    return slug or "未命名"


def default_relative_path(kind: str, title: str, today: date | None = None) -> Path:
    if kind not in ALLOWED_KINDS:
        raise WriterPolicyError(f"不支持的输出类型: {kind}")
    stamp = (today or date.today()).strftime("%Y%m%d")
    return Path(kind) / f"{stamp}-{_safe_slug(title)}-v1.md"


def resolve_output_path(project_root: str | os.PathLike[str], relative_path: str | os.PathLike[str]) -> Path:
    root = _project_root(project_root)
    text_root = (root / TEXT_DIR_NAME).resolve()
    candidate = Path(relative_path).expanduser()
    target = candidate.resolve() if candidate.is_absolute() else (text_root / candidate).resolve()
    if not _is_relative_to(target, text_root) or _is_protected(target):
        raise WriterPolicyError("输出只能位于当前项目的 文本/ 目录，且不能指向知识库源目录")
    return target


def _require_frontmatter(content: str) -> None:
    if not isinstance(content, str) or not content.lstrip().startswith("---\n"):
        raise WriterPolicyError("写入内容必须以 YAML frontmatter 开始")


def _atomic_write(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, newline="\n") as temp:
        temp.write(content)
        temp_path = Path(temp.name)
    try:
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_markdown_impl(
    project_root: str | os.PathLike[str],
    content: str,
    relative_path: str | os.PathLike[str],
    *,
    overwrite: bool = False,
) -> Path:
    _require_frontmatter(content)
    target = resolve_output_path(project_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError(f"文件已存在；只有用户明确要求覆盖时才可写入: {target}")
    _atomic_write(target, content)
    return target


def _append_markdown_impl(
    project_root: str | os.PathLike[str], content: str, relative_path: str | os.PathLike[str]
) -> Path:
    target = resolve_output_path(project_root, relative_path)
    if not target.exists():
        raise FileNotFoundError(f"不能追加到不存在的文件: {target}")
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return target


def create_index_content(title: str, entries: Iterable[str]) -> str:
    lines = [
        "---",
        "type: knowledge-index",
        f'topic: "{title}"',
        "agent_mode: production",
        "evidence_status: kb-grounded",
        "---",
        "",
        f"# {title}",
        "",
    ]
    lines.extend(f"- {entry}" for entry in entries)
    return "\n".join(lines) + "\n"


write_markdown = _write_markdown_impl
append_markdown = _append_markdown_impl


def register_tools(mcp):
    @mcp.tool()
    def write_markdown(
        project_root: str,
        content: str,
        relative_path: str = "",
        kind: str = "笔记",
        title: str = "未命名",
        overwrite: bool = False,
    ) -> dict:
        """Write a frontmatter-bearing Markdown artifact under <project-root>/文本 only."""
        relative = Path(relative_path) if relative_path else default_relative_path(kind, title)
        target = _write_markdown_impl(project_root, content, relative, overwrite=overwrite)
        return {"file": str(target), "created": not overwrite, "relative_path": str(relative).replace("\\", "/")}

    @mcp.tool()
    def append_markdown(project_root: str, relative_path: str, content: str) -> dict:
        """Append text to an existing Markdown artifact under <project-root>/文本 only."""
        target = _append_markdown_impl(project_root, content, relative_path)
        return {"file": str(target), "appended": True}

    @mcp.tool()
    def create_index(
        project_root: str,
        title: str,
        entries: list[str],
        relative_path: str = "",
        overwrite: bool = False,
    ) -> dict:
        """Create a Markdown index under <project-root>/文本 only."""
        relative = Path(relative_path) if relative_path else default_relative_path("证据包", title)
        target = _write_markdown_impl(project_root, create_index_content(title, entries), relative, overwrite=overwrite)
        return {"file": str(target), "entry_count": len(entries), "relative_path": str(relative).replace("\\", "/")}

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Restricted knowledge-base artifact writer")
    parser.parse_args()
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("kb-writer")
    register_tools(mcp)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
