from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import abstract_lookup


class AbstractLookupTests(unittest.TestCase):
    def test_reconstruct_openalex_abstract_orders_word_positions(self) -> None:
        inverted_index = {
            "abstract": [2],
            "A": [0],
            "short": [1],
        }

        self.assertEqual(
            abstract_lookup.reconstruct_abstract(inverted_index),
            "A short abstract",
        )

    def test_clean_text_removes_jats_markup_and_decodes_entities(self) -> None:
        raw = "<jats:p>Objective: assess &amp; compare.</jats:p>\n <jats:p>Second line.</jats:p>"

        self.assertEqual(
            abstract_lookup.clean_text(raw),
            "Objective: assess & compare. Second line.",
        )

    def test_record_is_verified_only_with_title_and_abstract(self) -> None:
        self.assertTrue(abstract_lookup.is_verified_record({"title": "Paper", "abstract": "Text"}))
        self.assertFalse(abstract_lookup.is_verified_record({"title": "Paper", "abstract": ""}))
        self.assertFalse(abstract_lookup.is_verified_record({"title": "", "abstract": "Text"}))

    def test_resolver_uses_crossref_when_openalex_has_no_abstract(self) -> None:
        def fake_json(url: str, **_: object) -> dict:
            if "api.openalex.org" in url:
                return {
                    "display_name": "OpenAlex title",
                    "abstract_inverted_index": None,
                }
            if "api.crossref.org" in url:
                return {
                    "message": {
                        "title": ["Crossref title"],
                        "abstract": "<jats:p>Public abstract from Crossref.</jats:p>",
                    }
                }
            raise AssertionError(f"unexpected URL: {url}")

        result = abstract_lookup.resolve_record(
            doi="10.1234/example",
            fetch_json_fn=fake_json,
        )

        self.assertEqual(result["title"], "OpenAlex title")
        self.assertEqual(result["abstract"], "Public abstract from Crossref.")
        self.assertEqual(result["abstract_source"], "crossref")
        self.assertEqual(result["abstract_status"], "verified")
        self.assertEqual(
            [item["source"] for item in result["source_attempts"]],
            ["openalex", "crossref"],
        )

    def test_resolver_marks_missing_abstract_without_fabricating_text(self) -> None:
        def empty_json(_: str, **__: object) -> dict:
            return {}

        result = abstract_lookup.resolve_record(
            doi="10.1234/example",
            fetch_json_fn=empty_json,
        )

        self.assertEqual(result["abstract"], "")
        self.assertEqual(result["abstract_source"], "")
        self.assertEqual(result["abstract_status"], "missing")
