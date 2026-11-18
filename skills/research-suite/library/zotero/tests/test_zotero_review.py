import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import zotero_review as review


class ZoteroReviewTests(unittest.TestCase):
    def test_collect_pages_follows_all_child_pages(self):
        calls = []
        pages = {
            0: ([{"key": "A"}, {"key": "B"}], {"Total-Results": "3"}),
            2: ([{"key": "C"}], {"Total-Results": "3"}),
        }

        def fetch_page(start, limit):
            calls.append((start, limit))
            return pages.get(start, ([], {"Total-Results": "3"}))

        collect_pages = getattr(review, "collect_pages", None)
        self.assertTrue(callable(collect_pages), "collect_pages must support paginated API results")
        rows, total = collect_pages(fetch_page, page_size=2)
        self.assertEqual(["A", "B", "C"], [row["key"] for row in rows])
        self.assertEqual(3, total)
        self.assertEqual([0, 2], [start for start, _ in calls])

    def test_select_candidate_resolves_ambiguous_markdown(self):
        candidates = [
            {"rank": 0, "attachmentKey": "ZIP1", "entry": "scan/page.md"},
            {"rank": 0, "attachmentKey": "ZIP2", "entry": "full.md"},
        ]
        select_candidate = getattr(review, "select_candidate", None)
        self.assertTrue(callable(select_candidate), "select_candidate must support explicit selection")
        selected = select_candidate(candidates, attachment_key="ZIP2", entry_name="full.md")
        self.assertEqual("ZIP2", selected["attachmentKey"])
        with self.assertRaisesRegex(review.ZoteroError, "Multiple Markdown candidates"):
            select_candidate(candidates)

    def test_markdown_command_accepts_explicit_candidate(self):
        try:
            args = review.build_parser().parse_args(
                [
                    "markdown",
                    "ITEMKEY1",
                    "--attachment-key",
                    "ZIPKEY01",
                    "--entry",
                    "full.md",
                ]
            )
        except SystemExit as exc:
            self.fail(f"markdown command rejected explicit candidate options: {exc}")
        self.assertEqual("ZIPKEY01", args.attachment_key)
        self.assertEqual("full.md", args.entry)

    def test_read_linked_markdown_preserves_explicit_selection(self):
        parent = {
            "key": "ITEMKEY1",
            "data": {"itemType": "journalArticle", "title": "Exact title", "DOI": ""},
        }
        attachment = {
            "key": "ZIPKEY01",
            "data": {
                "key": "ZIPKEY01",
                "itemType": "attachment",
                "title": "cache.zip",
                "filename": "cache.zip",
                "contentType": "application/zip",
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "cache.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("full.md", "# Exact title\n\nbody\n")

            def api_response(path):
                if path == "/api/users/0/items/ITEMKEY1":
                    return parent, {}
                if path.startswith("/api/users/0/items/ITEMKEY1/children?"):
                    return [attachment], {"Total-Results": "1"}
                self.fail(f"unexpected Zotero route: {path}")

            with (
                patch.object(review, "api_json", side_effect=api_response),
                patch.object(review, "attachment_file_path", return_value=zip_path),
            ):
                _, source, markdown = review.read_linked_markdown(
                    "ITEMKEY1",
                    attachment_key="ZIPKEY01",
                    entry_name="full.md",
                )
                _, auto_source, auto_markdown = review.read_linked_markdown("ITEMKEY1")

        self.assertEqual("ZIPKEY01", source["attachmentKey"])
        self.assertEqual("full.md", source["entry"])
        self.assertIn("body", markdown)
        self.assertEqual("ZIPKEY01", auto_source["attachmentKey"])
        self.assertEqual("full.md", auto_source["entry"])
        self.assertIn("body", auto_markdown)

    def test_identity_check_matches_title_and_doi(self):
        title = "Opportunities and challenges for geologic CO2 sequestration in carbonate reservoirs: A review"
        markdown = (
            "# Opportunities and challenges for geologic $CO_{2}$ sequestration "
            "in carbonate reservoirs: A review\n\n"
            "DOI: https://doi.org/10.1016/j.ijggc.2025.104342\n"
        )
        check_identity = getattr(review, "check_document_identity", None)
        self.assertTrue(callable(check_identity), "document identity must be checked before using Markdown")
        result = check_identity(title, "10.1016/j.ijggc.2025.104342", markdown)
        self.assertEqual("matched", result["status"])
        self.assertTrue(result["doiMatch"])

    def test_identity_check_flags_mismatched_document(self):
        check_identity = getattr(review, "check_document_identity", None)
        self.assertTrue(callable(check_identity), "document identity must be checked before using Markdown")
        result = check_identity("Expected article title", "10.1234/expected", "# Unrelated article\n\nBody")
        self.assertEqual("mismatch", result["status"])

    def test_identity_check_rejects_title_conflict_even_with_matching_metadata_doi(self):
        markdown = "# Unrelated article\n\nDOI: 10.1234/expected\n\nBody"
        result = review.check_document_identity("Expected article title", "10.1234/expected", markdown)
        self.assertEqual("mismatch", result["status"])

    def test_identity_check_does_not_use_doi_from_references(self):
        markdown = (
            "# Unrelated article\n\n## Abstract\nOther work.\n\n"
            "## References\nA cited work. DOI: 10.1234/expected\n"
        )
        result = review.check_document_identity("Expected article title", "10.1234/expected", markdown)
        self.assertEqual("mismatch", result["status"])
        self.assertFalse(result["doiMatch"])

    def test_identity_check_does_not_use_doi_from_nonstandard_body_section(self):
        markdown = "An article without an H1 title.\n\n## Methods\nIt cites DOI 10.1234/expected here."
        result = review.check_document_identity(None, "10.1234/expected", markdown)
        self.assertNotEqual("matched", result["status"])
        self.assertFalse(result["doiMatch"])

    def test_search_items_supports_result_offsets(self):
        items = [
            {"key": f"KEY{index}", "data": {"itemType": "journalArticle", "title": f"Title {index}"}}
            for index in range(5)
        ]
        with patch.object(review, "api_json", return_value=(items, {"Total-Results": "5"})):
            result = review.search_items("topic", max_results=2, start_result=2)
        self.assertEqual(["KEY1", "KEY2"], [item["key"] for item in result["items"]])
        self.assertTrue(result["truncated"])
        self.assertEqual(4, result["nextResult"])

    def test_search_items_omits_everything_mode_for_local_api(self):
        with patch.object(review, "api_json", return_value=([], {"Total-Results": "0"})) as request:
            review.search_items("no-match", max_results=1)
        self.assertNotIn("qmode=everything", request.call_args.args[0])

    def test_search_output_is_bounded_and_can_continue_long_abstract(self):
        result = {
            "query": "topic",
            "totalSearchHits": 2,
            "startResult": 1,
            "returned": 2,
            "truncated": False,
            "nextResult": None,
            "items": [
                {"key": "KEY1", "title": "Large abstract", "abstractNote": "a" * 20000},
                {"key": "KEY2", "title": "Next article", "abstractNote": "short"},
            ],
        }
        page = review.bounded_search_result(result)
        rendered = json.dumps(page, ensure_ascii=False, indent=2)
        self.assertLessEqual(len(rendered), review.MAX_OUTPUT_CHARS)
        self.assertTrue(page["items"][0]["abstractTruncated"])
        self.assertEqual(1, page["nextResult"])
        self.assertGreater(page["nextAbstractStart"], 0)

    def test_candidate_error_pages_are_bounded_and_number_selects_any_entry(self):
        candidates = [
            {"rank": 0, "attachmentKey": f"ZIP{index}", "entry": f"folder/document-{index}.md"}
            for index in range(1, 501)
        ]
        with self.assertRaises(review.ZoteroError) as first_page_error:
            review.select_candidate(candidates)
        first_message = str(first_page_error.exception)
        self.assertLessEqual(len(first_message), review.MAX_OUTPUT_CHARS)
        self.assertIn("--candidate-start 101", first_message)

        with self.assertRaises(review.ZoteroError) as later_page_error:
            review.select_candidate(candidates, candidate_start=101)
        self.assertIn("ZIP101:folder/document-101.md", str(later_page_error.exception))

        selected = review.select_candidate(candidates, candidate_number=500)
        self.assertEqual("ZIP500", selected["attachmentKey"])

    def test_attachment_failure_details_are_bounded(self):
        failures = [f"archive-{index}: {'x' * 1000}" for index in range(100)]
        details = review.format_attachment_failures(failures)
        self.assertLessEqual(len(details), review.MAX_OUTPUT_CHARS - 512)
        self.assertIn("additional attachment errors omitted", details)

    def test_markdown_can_be_read_in_bounded_line_pages(self):
        page_markdown = getattr(review, "page_markdown", None)
        self.assertTrue(callable(page_markdown), "Markdown output must support bounded line pages")
        page = page_markdown("one\ntwo\nthree\nfour\n", start_line=2, max_lines=2)
        self.assertEqual(2, page["startLine"])
        self.assertEqual(3, page["endLine"])
        self.assertEqual(4, page["totalLines"])
        self.assertTrue(page["hasMore"])
        self.assertEqual("two\nthree", page["text"])

    def test_markdown_page_caps_long_lines_and_returns_column_cursor(self):
        page_markdown = getattr(review, "page_markdown", None)
        self.assertTrue(callable(page_markdown), "Markdown output must support bounded character pages")
        page = page_markdown(
            "x" * (review.MAX_OUTPUT_CHARS + 20),
            start_line=1,
            max_lines=120,
        )
        self.assertLessEqual(len(page["text"]), review.MAX_OUTPUT_CHARS)
        self.assertTrue(page["hasMore"])
        self.assertEqual(1, page["nextStartLine"])
        self.assertEqual(review.MAX_OUTPUT_CHARS + 1, page["nextStartColumn"])

    def test_heading_pages_are_bounded_and_report_continuation(self):
        page_headings = getattr(review, "page_headings", None)
        self.assertTrue(callable(page_headings), "heading output must support bounded pages")
        headings = review.markdown_headings("\n".join(f"## Heading {index}" for index in range(100)))
        page = page_headings(headings, start_heading=1, max_chars=300)
        self.assertLessEqual(len(page["text"]), 300)
        self.assertTrue(page["hasMore"])
        self.assertGreater(page["nextHeading"], page["endHeading"])


if __name__ == "__main__":
    unittest.main()
