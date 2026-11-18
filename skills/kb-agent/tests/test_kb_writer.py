import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR))

from kb_writer_mcp import (  # noqa: E402
    WriterPolicyError,
    default_relative_path,
    register_tools,
    resolve_output_path,
    write_markdown,
)


DOCUMENT = "---\ntype: note\n---\n\nLocal-library grounded text.\n"


class ToolRecorder:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


class KnowledgeBaseWriterTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name) / "project"
        self.project.mkdir()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_default_relative_path_uses_text_kind_and_version(self):
        relative = default_relative_path("摘要", "A/B: Local Paper", today=date(2026, 8, 18))

        self.assertEqual(relative.as_posix(), "摘要/20260818-A-B-Local-Paper-v1.md")

    def test_resolve_output_path_keeps_relative_target_under_text_directory(self):
        target = resolve_output_path(self.project, "笔记/topic.md")

        self.assertEqual(target, self.project / "文本" / "笔记" / "topic.md")

    def test_resolve_output_path_rejects_traversal(self):
        with self.assertRaises(WriterPolicyError):
            resolve_output_path(self.project, "../outside.md")

    def test_resolve_output_path_rejects_source_library_target(self):
        with self.assertRaises(WriterPolicyError):
            resolve_output_path(self.project, "../01-library/source.md")

    def test_write_markdown_creates_text_tree_without_overwriting(self):
        target = write_markdown(self.project, DOCUMENT, "笔记/local-note.md")

        self.assertEqual(target, self.project / "文本" / "笔记" / "local-note.md")
        self.assertEqual(target.read_text(encoding="utf-8"), DOCUMENT)
        with self.assertRaises(FileExistsError):
            write_markdown(self.project, DOCUMENT, "笔记/local-note.md")

    def test_write_markdown_rejects_content_without_frontmatter(self):
        with self.assertRaises(WriterPolicyError):
            write_markdown(self.project, "missing frontmatter", "笔记/bad.md")

    def test_register_tools_exposes_only_write_operations(self):
        recorder = ToolRecorder()

        register_tools(recorder)

        self.assertEqual(set(recorder.tools), {"write_markdown", "append_markdown", "create_index"})


if __name__ == "__main__":
    unittest.main()
